import requests
from collections import Counter

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
categories = [l.get('category', '').strip() for l in lessons]
c = Counter(categories)
print("Unique categories and counts:")
for cat, count in c.most_common():
    print(f"  '{cat}': {count}")
