# Release Notes — create-flotilla v0.5.1

## Release Summary

**Version**: 0.5.1
**Date**: 2026-06-02
**Status**: Released

Security patch. No functional changes to the fleet dispatcher or profile pack system.

---

## Security Fixes

### Auth gate fail-closed (CVE-BRT-001)

The Fleet Hub server previously allowed all traffic when neither Google OAuth nor a bearer token was configured. The gate now blocks non-GET requests in this state. Authentication is now required in all deployment modes; local dev falls back to loopback-only access.

Three-tier auth order: Google OAuth → Bearer token (`FLEET_API_SECRET`) → loopback-only.

### repo_path traversal (CVE-BRT-002)

The `/fleet/api/setup` route accepted arbitrary `repo_path` values, allowing writes outside the intended workspace. Paths are now validated against `FLEET_WORKSPACE_ROOT` and rejected if they escape it.

### Port binding (CVE-BRT-003)

`docker-compose.yml` was binding fleet-hub to `0.0.0.0:8787`, exposing the dashboard on all network interfaces. The default is now `127.0.0.1:8787`. Override with `FLEET_BIND_HOST` if remote access is intentional.

### Public route whitelist (CVE-BRT-004)

`/fleet/api/config/demo` and `/fleet/api/config/growth` are explicitly whitelisted for unauthenticated GET. All other endpoints require auth.

---

## New Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `FLEET_API_SECRET` | _(none)_ | Bearer token for non-OAuth deployments |
| `FLEET_WORKSPACE_ROOT` | _(none)_ | Restricts repo_path writes to this directory tree |
| `FLEET_BIND_HOST` | `127.0.0.1` | Network interface the server binds to |

**Upgrade action required**: set `FLEET_API_SECRET` and `FLEET_WORKSPACE_ROOT` in your `.env` before deploying to any non-localhost environment.

---

## How to Upgrade

```bash
npx create-flotilla@0.5.1 <project-dir>
```

Or for an existing install:

```bash
git pull origin master
bash fleet/sync_to_fleet.sh --restart
```

---

*Security report by Bertie. Patch by Clau.*
