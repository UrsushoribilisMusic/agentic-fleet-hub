import requests
import json

PB_URL = "http://localhost:8090/api/collections/lessons/records"

resp = requests.get(f"{PB_URL}?perPage=10")
items = resp.json().get("items", [])
for i, item in enumerate(items):
    print(f"=== Lesson {i+1} ===")
    print(json.dumps(item, indent=2))
