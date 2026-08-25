# Codi Worklog — WP1 C-106

Task: WP1 C-106 Job status & APNs completion push.

Plan:
- Inspect C-105 Canis ingestion pipeline, schema, and API surfaces.
- Add durable per-document/job processing status that the console/API can poll while ingestion runs.
- Add APNs device registration and completion notification dispatch with safe no-op behavior when APNs credentials are absent.
- Normalize ingestion failures into human-readable reasons and keep stack traces out of API/UI status payloads.
- Add focused tests for processing, completion notification, and failure surfaces.
