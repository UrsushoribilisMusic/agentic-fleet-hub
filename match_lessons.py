import requests
import json
import os

PB_URL = "http://localhost:8090/api/collections/lessons/records"

def fetch_all_lessons():
    records = []
    page = 1
    per_page = 100
    while True:
        url = f"{PB_URL}?page={page}&perPage={per_page}"
        resp = requests.get(url)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        records.extend(items)
        if len(items) < per_page:
            break
        page += 1
    return records

lessons = fetch_all_lessons()

ledger_path = "/Users/miguelrodriguez/projects/agentic-fleet-hub/AGENTS/LESSONS/ledger.json"
if os.path.exists(ledger_path):
    with open(ledger_path) as f:
        ledger = json.load(f)
    print(f"Loaded {len(ledger)} entries from ledger.json")
    
    # Try matching by title or id
    matched = 0
    for item in ledger:
        # Match by id or title
        match = None
        for l in lessons:
            id_item = item.get('id')
            id_l = l.get('id')
            title_item = item.get('title', '').strip().lower()
            title_l = l.get('title', '').strip().lower()
            if (id_item and id_l and id_item == id_l) or (title_item and title_l and title_item == title_l):
                match = l
                break
        if match:
            matched += 1
            print(f"Matched: '{item['title']}'")
            print("  Ledger: ", {k: item[k] for k in ['symptom', 'root_cause', 'lesson']})
            print("  PB:     ", {k: match.get(k) for k in ['content', 'rationale', 'decision', 'outcome']})
    print(f"Total matched: {matched} / {len(ledger)}")
else:
    print("ledger.json not found")
