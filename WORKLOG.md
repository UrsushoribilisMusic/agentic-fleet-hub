# WORKLOG - Task 99: Release Flotilla v0.4.0

## Plan
1. **Sync Assets from Cloud Infra**: Copy the updated dashboard (Schichtplan, aggregate stats) from `salesman-cloud-infra/opt/salesman-api/fleet/` to `agentic-fleet-hub/package/dashboard/engineering/`.
2. **Sync Scripts from Root**: Update `package/scripts/dispatcher.py` and other core scripts with the latest v4 logic.
3. **Bump Version**: Update `package/package.json` and `package/README.md` to `0.4.0`.
4. **Update Release Notes**: Create `RELEASE_NOTES_v0.4.0.md` with detailed feature list.
5. **Update MISSION_CONTROL.md**: Reflect the new release status.
6. **Verify Bundle**: Run `npm run verify:dry-run` to ensure the package is valid.
7. **Peer Review**: Hand off to another agent for approval.

## Execution
- [ ] Sync dashboard assets
- [ ] Sync scripts
- [ ] Bump version in package.json
- [ ] Bump version in README.md
- [ ] Create RELEASE_NOTES_v0.4.0.md
- [ ] Update MISSION_CONTROL.md
- [ ] Run verify:dry-run
