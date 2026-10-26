# Fleet execution policy — October 26, 2026

- Gem's sole autonomous model launcher is `fleet.dispatcher`. The legacy hourly
  Gem launchd job is disabled; its wrapper returns without a model when called
  without a task. An explicit dispatcher task skips the autonomous heartbeat gate.
- Misty's subscription is paused (`available: false`). The legacy `gemma` slot
  is **Qwen Coder**, also paused; `qwen` maps to `gemma` for availability checks.
  Preserve queued tasks rather than reassigning them because of pauses/quotas.
- `fleet/scheduler_policy.py` shares availability and provider reset-time parsing
  between dispatcher and wrappers. Quota retries use `Resets in …` plus two
  minutes of margin; unavailable agents must not be treated as offline failures.
- Codi's wrapper flushes pending PB writes *before* starting an LLM. A rejected
  or unavailable write stays queued and stops another model session.
- Codi approval PATCHes require a recorded independent approval newer than the
  task's last update and cited commits reachable from canonical main/master
  branches. No self-approval; no PC-only ticket-name or one-hour restriction.
  Implementation progress still requires a task-linked canonical commit.
- A successful PB query is authoritative for heartbeat relevance. MC text is
  fallback context when PB is unavailable. Own `peer_review` tasks cannot cause
  self-review; another agent's peer-review work can wake the reviewer.
- Source is in the repo's `fleet/`; launchd executes `~/fleet/` copies. Sync
  policy, wrappers and the PB flusher together. Avoid broad deployments that
  restore old runtime files or re-enable paused Qwen/Misty jobs.
- Codi's canonical launchd plist is in `fleet/launchd/`. XML comments must not
  contain `--`; use `plutil -lint` before copying or reloading.
- Regression suite: `python3 -m unittest discover -s fleet/tests -v`.
