# Changelog

## [0.2.0] - 2026-03-16

### Added
- Heartbeat dot tooltips and mock status for demo and growth dashboards
- Demo intercept modal for write actions with Big Bear CTA
- GitHub Issues ↔ PocketBase two-way sync (github_sync.py launchd service)
- Dynamic Telegram bot commands from fleet_meta.json (9 commands: /clau /gem /codi /ask /spec /go /status /tasks /help)
- Misty (Mistral Vibe) onboarding: MISTRAL.md mandate, heartbeat protocol, fleet workspace
- Package sync: dashboard assets, plists, and scripts to package/scripts/ and package/blueprint/
- Hybrid deployment support: fleet_push.py connector for local PocketBase → remote Fleet Hub
- Agent health monitoring: skill-based task reassignment on stale heartbeats (>30m)
- Deployment scenarios documentation: Local/Cloud/Hybrid comparison in README

### Changed
- Updated ARCHITECTURE.md to v0.2.0 with new component diagrams
- Improved demo and growth dashboard UI/UX with dark/light mode support
- Fleet Doctor: added Telegram/OpenClaw/GitHub Sync/Hybrid script verification
- Setup wizard: added deployment/integration steps for v0.2.0

### Fixed
- Fixed PocketBase bind conflict (removed duplicate com.flotilla.pocketbase service)
- Resolved Telegram bridge outbound truncation for messages >4096 characters
- Fixed dispatcher trusted directory error for Codi fleet invocation
- Fixed Codi launchd invocation with proper node path
- Fixed github_sync.py duplicate issue creation and non-atomic inbound import

## [0.1.0] - 2026-03-13

### Added
- Initial release of create-flotilla.
- Basic fleet management and dashboard features.
