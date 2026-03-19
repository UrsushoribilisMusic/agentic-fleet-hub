import sys
import json

data = json.load(sys.stdin)
print('Peer review tasks by agent:')

agents = {}
for item in data['items']:
    agent = item.get('assigned_agent')
    agents[agent] = agents.get(agent, 0) + 1

import pprint
pprint.pprint(agents)