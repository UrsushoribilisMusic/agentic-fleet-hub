import os
import sys
import json
import urllib.request
import urllib.error

def fetch_secret(name):
    try:
        # Assuming we are in agentic-fleet-hub/scripts/financial_ops/
        # The vault script is at agentic-fleet-hub/vault/agent-fetch.sh
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        script_path = os.path.join(repo_root, "vault", "agent-fetch.sh")
        import subprocess
        result = subprocess.run([script_path, name, "dev"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error fetching secret {name}: {e}")
        return None

def test_elevenlabs():
    print("\n--- ElevenLabs Test ---")
    api_key = fetch_secret("ELEVENLABS_API_KEY")
    if not api_key:
        print("ELEVENLABS_API_KEY missing")
        return

    url = "https://api.elevenlabs.io/v1/user/subscription"
    req = urllib.request.Request(url, headers={"xi-api-key": api_key})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Character count: {data.get('character_count')}")
            print(f"Character limit: {data.get('character_limit')}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.read().decode()}")
    except Exception as e:
        print(f"Error: {e}")

def test_runway():
    print("\n--- Runway Test ---")
    api_key = fetch_secret("RUNWAYML_API_SECRET")
    if not api_key:
        print("RUNWAYML_API_SECRET missing")
        return

    # Using the endpoint from WORKLOG.md
    url = "https://api.dev.runwayml.com/v1/organization"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Organization data: {json.dumps(data, indent=2)}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.read().decode()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_elevenlabs()
    test_runway()
