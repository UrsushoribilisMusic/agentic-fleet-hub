import sys
import json

data = json.load(sys.stdin)
print('Total tasks in system:', data['totalItems'])

status_counts = {}
for item in data['items']:
    status = item.get('status')
    status_counts[status] = status_counts.get(status, 0) + 1

print('Status counts:')
import pprint
pprint.pprint(status_counts)