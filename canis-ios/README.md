# canis-ios has moved out of this monorepo

The **Canis iOS app** now lives in its own repository:

- **GitHub:** https://github.com/UrsushoribilisMusic/canis-ios (private)
- **Local path:** `~/projects/canis-ios`

## Why

Split out on **2026-09-24** so external collaborators (BitForge) can be given access to
just the app, without exposing the rest of the fleet monorepo. This also makes it the
single source of truth and prevents the two copies from diverging.

## For the fleet and for humans

**Do all Canis work in `~/projects/canis-ios` from now on.** New CANIS-* tickets should
reference that path, not `agentic-fleet-hub/canis-ios`. The remote uses HTTPS under the
same account, so the usual gh credentials push there — no extra auth setup.

This directory is only a pointer. The pre-split code and its history are preserved in this
monorepo's git history (before this commit) and, going forward, in the standalone repo.
