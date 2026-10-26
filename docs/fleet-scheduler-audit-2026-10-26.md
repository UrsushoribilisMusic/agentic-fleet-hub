# Codi — scheduler audit, 2026-10-26

Read-only inspection of launchd registrations, runtime scripts, logs, the Muse
onboarding commit and live PocketBase records. No agents were launched for the
audit, no task statuses were changed, and no schedules were disabled.

## Findings

### Gem has two independent scheduling paths

Loaded `com.flotilla.heartbeat.gem` invokes `~/fleet/gem/heartbeat_wrapper.sh`
hourly. Loaded `fleet.dispatcher` invokes `agy` directly for assigned todo tasks.
The wrapper has a checksum/relevance gate but does not consult the dispatcher's
agent-failure cooldown. Neither path shares an agent execution lock with the
other; the dispatcher's running-agent map covers only its own child processes.

Observed launches, October 24 through approximately 10:20 on October 26, local
log dates (October 25 contains the daylight-saving transition):

| Date | Gem hourly-wrapper CLI attempts | Dispatcher Gem attempts |
|---|---:|---:|
| October 24 | 9 | 1 |
| October 25 | 6 | 1 |
| October 26, morning | 3 | 1 |
| Total | 18 | 3 |

Of these 21 attempts, wrapper exit codes show 11 successful exits and 7 quota
rejections. Dispatcher records show 2 quota rejections and a 20-minute timeout
on TSC-1. Exit zero does not establish useful work or exact token usage; quota
rejections do not establish token consumption. Separately, 42 hourly wrapper
checks skipped the CLI entirely. Those checks are ordinary Python/shell work.

Gem's current provider errors report `Individual quota reached`. The October 26
07:00 wrapper attempt reported approximately 118 hours until reset. The
dispatcher imposes a fixed 12-hour quota cooldown, while the wrapper ignores
that cooldown altogether. This leads to predictable retries before reset.

### Repeated Codi reviews caused by a rejected status write

Task `w282xy01di0whh3` (TSC-4) remains `peer_review`, with 7 Codi approval
comments since October 24. The queued PATCH to `approved` remains in
`~/fleet/codi/pb_pending_writes.json`.

`~/fleet/codi/pb_flush.py` rejects forward-status changes unless the task title
contains a `PC-N` or `#N` identifier and finds a recent matching commit on `main`.
TSC-4 cannot pass that legacy title rule. The runtime error log explicitly
reports `REJECT w282xy01di0whh3 (no PC-N/#N in title to verify against)`.
Approval comments are posted successfully, but the state transition is not;
subsequent heartbeat sessions perform the review again. This is avoidable
model work, not just a lightweight scheduler poll.

### Compilation tasks have real outstanding work

TSC-1 and TSC-2 currently remain `todo` for Gem. Existing private uploads and
rendered media are recorded, but independent reviews identify unfinished
publication/dashboard closure, plus TSC-1 build-source integration. Do not
rebuild or upload duplicates, or mark these tasks completed without addressing
the review. Human-dependent release steps should be represented as waiting for
the human, rather than repeatedly dispatching an unavailable agent.

### Muse onboarding is not the origin of Gem's quota exhaustion

Commit `5388de93`, October 24 at 09:36 CEST, adds Muse command/metadata/aliases
and task-prompt handling. It does not modify Gem's command or hourly wrapper.
Gem's quota failures were already present on October 23 at 11:00, before this
commit. No Muse dispatcher launches or loaded Muse launchd job were found in
the inspected records. This does not measure interactive Muse usage.

### Other agents and a configuration defect

Misty and Gemma continue frequent scheduler checks, but their October 24–26
logs show the gate skipping the model. Frequent checks alone are not evidence
of LLM usage. Clau's inspected dispatcher launches were actual task assignments.

The on-disk `com.flotilla.heartbeat.codi.plist` is malformed XML: a comment
contains `--add-dir`, and XML comments cannot contain `--`. The already loaded
job still invokes the wrapper, but reloading this file can fail. Fix and lint
the file before the next reload/reboot. This is distinct from the PB write
guard, which is the confirmed cause of the repeated TSC-4 reviews.

## Recommended repair order

1. Share agent availability/reset-time checks and an execution lock across the
   dispatcher and heartbeat wrappers. Prefer one execution owner per agent.
2. Parse the provider's reset hint instead of applying an unconditional 12-hour
   retry. Treat quota exhaustion as an explicit unavailable state in every path.
3. Replace Codi's PC-only guard with project-aware verification that supports
   legitimate peer reviews of existing commits, and retain no-self-approval
   checks. Surface a failed PATCH as a blocked transition, not another review.
4. Deduplicate already-recorded reviews until the source commit or acceptance
   criteria change; keep human-dependent publication tasks out of the todo loop.
5. Correct/lint the Codi launchd plist before reloading it.

These logs establish wasted work and premature retries. They do not establish
what fraction of Gem's total provider quota was consumed by autonomous versus
interactive sessions; no provider billing/usage ledger was inspected.

Evidence paths: `~/fleet/logs/gem.log`, `gem_err.log`, `dispatcher.log`,
`codi.log`, `codi_err.log`; runtime `~/fleet/dispatcher.py`,
`heartbeat_check.py`, `gem/heartbeat_wrapper.sh`, `codi/pb_flush.py`; canonical
dispatcher state under `agentic-fleet-hub/fleet/logs/`; live read-only PocketBase
task/comment records. Duplicate dispatcher stdout/file logs were not double-counted.
