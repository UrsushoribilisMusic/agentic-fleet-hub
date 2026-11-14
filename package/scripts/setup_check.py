"""setup_check.py: quick health check for a new Flotilla install.

    python3 scripts/setup_check.py

Checks that PocketBase answers and, if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID are
set (for example via your vault), sends a test message to the human manager.
"""
import requests

from flotilla_config import PB_URL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, WORKSPACE_DIR, MISSION_CONTROL_PATH


def check_pb():
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records", timeout=5)
        print(f"PocketBase {PB_URL}: HTTP {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"PocketBase error: {e}")
        return False


def check_workspace():
    ok = MISSION_CONTROL_PATH.exists()
    print(f"Workspace {WORKSPACE_DIR}: {'MISSION_CONTROL.md found' if ok else 'MISSION_CONTROL.md MISSING'}")
    return ok


def send_test_telegram():
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        print("Telegram: skipped (TELEGRAM_TOKEN / TELEGRAM_CHAT_ID not set)")
        return True
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": "Hello from Flotilla"}, timeout=10)
    print(f"Telegram: HTTP {r.status_code}")
    return r.ok


if __name__ == "__main__":
    results = [check_workspace(), check_pb(), send_test_telegram()]
    raise SystemExit(0 if all(results) else 1)
