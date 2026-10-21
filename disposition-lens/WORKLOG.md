# WORKLOG — jrd58rbigoj3mdu

**Task:** disposition-lens CWE-306 fix — hardcoded 0.0.0.0 bind + missing auth on /infer /voice /health  
**Branch:** task/jrd58rbigoj3mdu  
**Agent:** clau

## Plan

1. Add `DISPOSITION_LENS_TOKEN` bearer-token dependency to FastAPI (`fastapi.security.HTTPBearer`).
   - Token is read from env at startup. If unset, the service starts but all protected routes return 503 with a clear message (fail-closed).
   - Attach `Depends(_require_token)` to `POST /infer` and `POST /voice`.
2. Change default bind host from hardcoded `"0.0.0.0"` to `os.getenv("DISPOSITION_LENS_HOST", "127.0.0.1")`.
3. Remove `elevenlabs_configured` field from `/health` response (posture leak).

## Key decisions

- Auth is fail-closed: if `DISPOSITION_LENS_TOKEN` is not set, protected routes return 503 rather than allow anonymous access.
- `/health` (GET) left unauthenticated — operators need liveness probes. But ElevenLabs posture bit is dropped.
- No rate limiting in this PR (requires redis/starlette-limiter; out of scope for this fix pass).
