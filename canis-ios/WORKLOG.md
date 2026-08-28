# CANIS-I Worklog

Task: reroute on-device iOS disposition resolution to J-space only, matching the server `ENTROPY_GATE_ENABLED = False` behavior.

Plan:
- Locate the Swift disposition resolver and current entropy gate/blend path.
- Compare against `disposition-lens/disposition.py`.
- Add or use a feature flag that keeps the entropy gate disabled by default.
- Update focused tests or add parity coverage using identical score/entropy inputs.
- Run the available iOS/package verification for the touched surface.
