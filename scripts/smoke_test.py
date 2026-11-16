# ==============================================================
# scripts/smoke_test.py — Automated Pre-Deployment Smoke Test
# Validates backend health, endpoints, and data integrity
# ==============================================================
"""
Usage:
    python scripts/smoke_test.py [BASE_URL]

Examples:
    python scripts/smoke_test.py http://localhost:8000
    python scripts/smoke_test.py https://ai-factory-os-backend.onrender.com
"""

import sys
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

DEFAULT_BASE = "http://localhost:8000"
BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else DEFAULT_BASE


def test_endpoint(name: str, path: str, expected_key: str = None) -> bool:
    url = f"{BASE_URL}{path}"
    print(f"🔍 Testing [{name}] -> {url} ...", end=" ")
    try:
        req = Request(url, headers={"User-Agent": "AIFactoryOS-SmokeTest/1.0"})
        with urlopen(req, timeout=15) as resp:
            status = resp.status
            data = json.loads(resp.read().decode("utf-8"))

        if status == 200:
            if expected_key and expected_key not in data:
                print(f"⚠️ FAILED (Missing expected key: '{expected_key}')")
                return False
            print(f"✅ PASS (HTTP 200)")
            return True
        else:
            print(f"❌ FAILED (HTTP {status})")
            return False
    except HTTPError as e:
        print(f"❌ FAILED (HTTP {e.code}: {e.reason})")
        return False
    except URLError as e:
        print(f"❌ FAILED (Connection Error: {e.reason})")
        return False
    except Exception as e:
        print(f"❌ FAILED (Exception: {e})")
        return False


def run_smoke_tests():
    print("=" * 65)
    print(f"🏭 AI Factory OS — Automated Smoke Test Suite")
    print(f"Target URL: {BASE_URL}")
    print("=" * 65)

    checks = [
        ("Health Check", "/api/health", "status"),
        ("Active Machines List", "/api/machines", None),
        ("Simulation Engine Status", "/api/simulation/status", "is_running"),
        ("Active Alerts Queue", "/api/alerts?resolved=false", None),
        ("Business Financial Impact", "/api/business/impact", None),
    ]

    passed = 0
    for name, path, key in checks:
        if test_endpoint(name, path, key):
            passed += 1

    print("-" * 65)
    print(f"Results: {passed}/{len(checks)} endpoints responding successfully.")
    print("=" * 65)

    if passed == len(checks):
        print("🎉 ALL SMOKE TESTS PASSED! System is ready for deployment/evaluation.")
        sys.exit(0)
    else:
        print("⚠️ SOME CHECKS FAILED. Verify backend server is running and database is seeded.")
        sys.exit(1)


if __name__ == "__main__":
    run_smoke_tests()
