# ==============================================================
# scripts/seed_db.py — One-time database initialisation script
# ==============================================================
"""
Creates all tables and seeds the 6 factory machines from config.yaml.
Usage:
    python scripts/seed_db.py
"""

from __future__ import annotations
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import get_settings
from backend.database import SessionLocal, create_all_tables
from backend.models.machine import Machine


def seed_machines() -> None:
    """Insert the 6 configured machines if they don't exist yet."""
    cfg = get_settings()
    db = SessionLocal()
    try:
        existing = {m.name for m in db.query(Machine).all()}
        added = 0
        for mc in cfg.machines:
            if mc.name not in existing:
                machine = Machine(
                    id=mc.id,
                    name=mc.name,
                    type=mc.type,
                    location=mc.location,
                    status="idle",
                    demo_engine_id=mc.demo_engine_id,
                )
                db.add(machine)
                added += 1
                print(f"  + {mc.name} ({mc.type}) @ {mc.location}")
        db.commit()
        print(f"✅ Seeded {added} new machines ({len(existing)} already existed).")
    finally:
        db.close()


def main() -> None:
    print("🔧 Creating database tables...")
    create_all_tables()
    print("🌱 Seeding factory machines...")
    seed_machines()
    print("✨ Database readiness verified.")


if __name__ == "__main__":
    main()
