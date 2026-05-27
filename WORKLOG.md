CR-015 worklog

Task: fleet_push financial sync.

Plan:
1. Inspect the existing Fleet Hub snapshot push contract in package/scripts/fleet_push.py and the DO-facing handler in package/server/fleet-server.mjs.
2. Add financial PocketBase collections to build_snapshot(): watch_hours_ledger, cost_ledger, income_ledger, campaigns_snapshot.
3. Update the server snapshot handler to accept and cache those collections without breaking existing snapshot fields.
4. Restore scripts/financial_ops/youtube_watch_hours.py source in music-video-tool from the available bytecode/source context.
5. Run focused syntax/tests where available, then commit and push the hub changes to master and the restored source to music-video-tool master.
