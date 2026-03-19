import sys
import json

data = json.load(sys.stdin)
print('Total tasks assigned to misty:', data['totalItems'])

status_counts = {}
for item in data['items']:
    status = item.get('status')
    status_counts[status] = status_counts.get(status, 0) + 1

print('Status counts for misty:')
import pprint
pprint.pprint(status_counts)