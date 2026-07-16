# SM-017 Worklog

Task: Web Console dashboard page for `sm.flotilla.cc`.

Plan:
- Add a repo-tracked static dashboard file for Sovereign Mind with inline CSS and JS.
- Preserve the backend auth flow by gating on `GET /auth/verify` and redirecting unauthenticated users to `/auth/login`.
- Deploy the file to `/var/www/sm.flotilla.cc/index.html` on `robotsales`.
- Update Caddy so `/auth/*`, `/api/*`, and existing `/downloads/*` continue to reach the backend/static download handling, while normal web routes serve the dashboard from `/var/www/sm.flotilla.cc/`.
- Validate Caddy config and smoke-test the deployed domain.
