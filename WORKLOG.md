# WORKLOG - [CR-003][P0] Active campaigns viewer

## Task Description
Daily job (~10:00 CET) reads Google Ads campaign state, writes to `campaigns_snapshot` PocketBase collection.
Fields: `snapshot_date`, `campaign_name`, `status`, `daily_budget_chf`, `spend_7d_chf`, `locations_summary`, `audience_name`.
**CRITICAL**: Zero write operations to Google Ads.

## Plan
1. **Research & Discovery**
    - [ ] Inspect existing Google Ads scripts in `music-video-tool` (`tcr_ads_live_executor.py`, etc.) for API usage patterns.
    - [ ] Verify PocketBase `campaigns_snapshot` collection schema.
    - [ ] Locate Google Ads credentials in Infisical via `vault/agent-fetch.sh`.
2. **Implementation**
    - [ ] Develop `cr_ads_snapshot.py` in `music-video-tool/scripts/` (or similar).
    - [ ] Implement `GoogleAdsClient` initialization (read-only).
    - [ ] Fetch active campaigns and their metrics.
    - [ ] Map metrics to PocketBase fields.
    - [ ] Ensure idempotency (snapshot per day).
3. **Verification**
    - [ ] Dry-run to verify data fetching without writing to PB.
    - [ ] Full-run and verify PB records.
    - [ ] Code review for any potential write paths (mandatory).

## Progress
- [x] Initialized task branch and WORKLOG.
