# PocketBase Operator Guide 

This guide documents the hardened startup and management procedures for the PocketBase instance powering a Flotilla fleet.

## Core Mandate: Single-Instance Ownership

PocketBase uses SQLite, which requires strict file locking. Running multiple instances against the same `pb_data` directory leads to `SQLITE_BUSY` errors, data corruption, and synchronization failures.

**NEVER** start PocketBase manually using the binary directly.

---

## Enforcement Layer: Binary Interceptor

As of April 2026, we have implemented an **Enforcement Layer** to prevent accidental direct execution of the PocketBase binary.

1.  The real binary has been renamed to `.pocketbase.bin.real`.
2.  The file `pocketbase` is now a protective shell script (interceptor).
3.  Any attempt to run `./pocketbase serve` without the wrapper will fail with an error message.

---

## The Safe Wrapper (`pocketbase_safe.sh`)

All interactions with PocketBase should go through the `pocketbase/pocketbase_safe.sh` script.

### Commands

| Command | Description |
| :--- | :--- |
| `./pocketbase_safe.sh status` | Checks if PB is running and identifies PIDs via port, data dir, and ps. |
| `./pocketbase_safe.sh start` | Performs safety checks and starts PB if no conflicts found. |
| `./pocketbase_safe.sh stop` | Gracefully stops all PB instances (SIGTERM then SIGKILL). |
| `./pocketbase_safe.sh restart` | Full stop followed by a safe start. |
| `./pocketbase_safe.sh clean-logs` | Stops PB, deletes the potentially huge `logs.db`, and restarts. |

### Safety Checks Performed
1. **Atomic Locking**: Uses `mkdir` for race-condition-proof locking.
2. **Port Check**: Verifies if port `8090` is in use by any process. **Automatically attempts to SIGTERM any rogue listener.**
3. **Data Directory Ownership**: Uses `lsof +D` to see if ANY process has files open in `pb_data` (prevents `SQLITE_BUSY`).
4. **Process Table Audit**: Scans `pgrep` for any rogue `pocketbase serve` commands.
5. **Log Size Check**: Warns if `logs.db` exceeds 1 GB (which causes high CPU usage).
6. **Improved Stale Lock Recovery**: Validates that the PID in the lockfile actually belongs to a PocketBase process before clearing it.

---

## Startup-Path Audit (Operational Hygiene)

To ensure single-instance stability, verify these paths are correctly configured. A rogue instance usually originates from one of these bypassed paths:

1. **launchd (System) - The Gold Standard**:
   - Primary service: `~/Library/LaunchAgents/fleet.pocketbase.plist`.
   - MUST point to `pocketbase_safe.sh`, NOT the binary.
   - `KeepAlive` should be `true`.
   - **AUDIT**: Run `launchctl list | grep pocketbase`. There should only be ONE entry (`fleet.pocketbase`).
   - **CLEANUP**: If you see `com.flotilla.pocketbase` or others, run `launchctl unload ~/Library/LaunchAgents/[name].plist`.

2. **Docker Compose (Local/Dev) - Port Conflicts**:
   - `docker-compose.yml` often contains a `pocketbase` service on port 8090.
   - While it uses a Docker volume (separate from host `pb_data`), it will prevent the host service from binding to the port.
   - **AUDIT**: Run `docker ps`. If a container is using port 8090, it will conflict.
   - **CLEANUP**: Run `docker compose stop pocketbase` if using the host-based fleet.

3. **Manual Agent Commands - Data Conflicts**:
   - Agents sometimes try to be "helpful" by starting PocketBase if they think it's down.
   - Our `pocketbase` binary is actually an interceptor script that blocks this.
   - **AUDIT**: Check `ps aux | grep pocketbase`. Look for any process NOT started by `pocketbase_safe.sh`.
   - **CLEANUP**: The wrapper now automatically detects and kills these, but if it fails, use `kill -9 [PID]`.

4. **External Projects (CRM-POC, etc.)**:
   - Other projects in `~/projects/` might have their own PocketBase setups.
   - Verify they are not configured to use port 8090 or the same `pb_data` path.

---

## Stability Verification (The "Acid Test")

To verify that the hardening is working as expected:

1. **Test Wrapper Conflict**:
   - While PB is running, run: `./pocketbase_safe.sh start`.
   - **Expected**: It should detect the lock, confirm the existing PID is healthy, and exit safely without killing the main instance.

2. **Test Rogue Interception**:
   - While PB is running, try: `./pocketbase serve`.
   - **Expected**: The interceptor script should block the command with a clear error message.

3. **Test Data Lockout**:
   - While PB is running, try: `./.pocketbase.bin.real serve --http 0.0.0.0:8091`.
   - **Expected**: This bypasses the interceptor and uses a different port, but uses the SAME data.
   - **Outcome**: This is what causes `SQLITE_BUSY`. The wrapper cannot prevent this if you call the binary directly, which is why the `pocketbase` file was replaced by the interceptor and the binary was hidden.

4. **Test Managed Recovery**:
   - Kill the PocketBase process: `kill -9 [PID]`.
   - **Expected**: `launchd` should restart it via `pocketbase_safe.sh` within 10-20 seconds. Check `~/fleet/logs/pocketbase_wrapper.log` for recovery trace.

---

## Troubleshooting

### "SQLITE_BUSY" Errors
1. Run `./pocketbase_safe.sh status`.
2. If multiple PIDs are shown or `lsof` reports data dir access, run `./pocketbase_safe.sh stop`.
3. The wrapper now automatically tries to clear the port, but manual `kill -9` may be needed if a process is hung.
4. Wait 5 seconds and run `./pocketbase_safe.sh start`.

### High CPU Usage (90%+)
PocketBase internal request logs can grow very large (e.g., 10GB+), causing SQLite performance degradation.
If `status` reports `logs.db` is large:
Run `./pocketbase_safe.sh clean-logs`

### Port 8090 Already in Use
If the wrapper reports a conflict on port 8090 but no PocketBase process is found, another application might be squatting on the port.
Check with: `lsof -i :8090`

### Database Backups
The `pb_data` directory contains:
- `data.db`: The primary database.
- `logs.db`: Audit logs.

Before performing manual backups or migrations, ALWAYS stop the service:
`./pocketbase_safe.sh stop`
