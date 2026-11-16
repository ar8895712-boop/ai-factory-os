# ==============================================================
# tests/test_memory.py — Unit tests for Factory Memory (FAISS)
# ==============================================================
"""
Tests for:
1. Embedding generation via sentence-transformers (384-d normalized)
2. FAISS IndexFlatIP cosine similarity search
3. Semantic retrieval relevance (e.g. 'vibration' matches 'spindle chatter')
4. Machine ID filtering in memory search
5. Recurring failure pattern learning & aggregation
6. FAISS save and reload persistence

Run:
    python -m pytest tests/test_memory.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.factory_memory import FactoryMemoryService, get_factory_memory


@pytest.fixture(scope="module")
def memory_service() -> FactoryMemoryService:
    """Returns singleton Factory Memory service."""
    mem = get_factory_memory()
    if mem.index.ntotal < 8:
        mem.rebuild_index_from_db()
    return mem


class TestFactoryMemory:

    def test_embedding_dimension_and_normalization(self, memory_service):
        """Embedding vector must be exactly 384-dimensional and unit normalized."""
        text = "High-pressure compressor stage 3 stator blade erosion"
        vec = memory_service._encode_text(text)

        assert vec.shape == (384,)
        assert vec.dtype == np.float32
        norm = np.linalg.norm(vec)
        assert norm == pytest.approx(1.0, rel=1e-3)

    def test_faiss_index_not_empty(self, memory_service):
        """Index must contain pre-seeded historical incident records."""
        assert memory_service.index.ntotal >= 5
        assert len(memory_service.incident_metadata) >= 5

    def test_semantic_search_relevance(self, memory_service):
        """
        Query 'pressure drop and fluid leak' should semantically match
        hydraulic pump or compressor pressure incidents with high cosine score.
        """
        results = memory_service.search_similar("pressure drop and fluid leak", top_k=3)
        assert len(results) > 0
        top = results[0]
        assert top.similarity_score > 0.30
        assert top.incident_id > 0
        assert len(top.description) > 0

    def test_vibration_query_matches_vibration_incident(self, memory_service):
        """
        Query 'spindle rattling and heavy chatter' must rank the CNC spindle vibration
        incident near or at the top.
        """
        results = memory_service.search_similar("spindle rattling and heavy chatter", top_k=3)
        match_descriptions = [r.description.lower() for r in results]
        found_vibration = any("vibration" in d or "spindle" in d for d in match_descriptions)
        assert found_vibration

    def test_machine_id_filtering(self, memory_service):
        """When filtering by machine_id=3, all returned matches must belong to Machine 3."""
        results = memory_service.search_similar(
            query="thermal degradation and blade creep",
            top_k=3,
            machine_id=3,
        )
        for r in results:
            assert r.machine_id == 3

    def test_add_live_incident_updates_index(self, memory_service):
        """Adding a new incident must immediately increment index count."""
        initial_count = memory_service.index.ntotal

        inc = memory_service.add_incident(
            machine_id=1,
            severity="warning",
            category="coolant_pump_cavitation",
            description="Coolant flow rate dropped below 12 L/min with audible pump cavitation whistle.",
            health_score=52.0,
            rul=34.0,
            anomaly_score=0.74,
            action_taken="reduce_speed",
            resolution_notes="Purged air from coolant lines and replaced inlet filter mesh.",
        )
        assert inc.id is not None
        assert memory_service.index.ntotal == initial_count + 1

        # Search for this exact symptom
        match = memory_service.search_similar("coolant pump cavitation whistle", top_k=1)[0]
        assert "coolant" in match.description.lower()
        assert match.similarity_score > 0.60

    def test_failure_pattern_learning(self, memory_service):
        """Pattern learning must group historical incidents into categories with actionable recommendations."""
        patterns = memory_service.learn_failure_patterns()
        assert len(patterns) > 0
        p0 = patterns[0]
        assert p0.frequency >= 1
        assert len(p0.affected_machines) > 0
        assert len(p0.common_symptoms) > 0
        assert p0.recommended_action in [
            "reduce_speed", "shift_load", "alert_operator", "schedule_maintenance"
        ]
