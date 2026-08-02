# FLOT-110 Worklog

Task: submission executor + launchd schedule.

Plan:

1. Add an importable executor module that loads and validates `manifest.json`, selects the next eligible pending post, calls the FLOT-109 composer, submits the correct Reddit post type, records a PB submission row, enqueues three verification checks, updates manifest attempt state, and sends one Telegram permalink alert.
2. Keep side effects injectable so tests can cover selection, cooldowns, flair handling, PB writes, verification queueing, and Telegram notification without live Reddit or Telegram calls.
3. Add a launchd plist for a 48-hour cadence at 09:00 with `RunAtLoad=true`, staggered from the existing 10:00 YouTube stats job.
4. Add focused tests for the acceptance path and no-operator skip cases.
5. Mirror any finished publisher files into the hub repo before final commit/push if needed by the fleet workflow.

Key decisions:

- Use the existing `flotilla_publisher.reddit_client` bundle/guard for Reddit operations.
- Use PocketBase REST for `publisher_submissions` and `publisher_verification_queue`; fall back to clear runtime errors if schema is missing.
- Do not use the existing untracked `publisher_alerts.py` because it contains hardcoded Telegram defaults. FLOT-110 will fetch Telegram credentials from environment or Infisical only.
- Do not attempt live posting in tests. The live fire remains a runtime command.
