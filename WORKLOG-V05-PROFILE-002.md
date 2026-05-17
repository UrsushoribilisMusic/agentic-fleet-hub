# WORKLOG — V05-PROFILE-002: Add Installer Support for Profile Directory and Zip Overlay

**Task ID:** fwxfhcprzb6g2oc  
**Sprint:** Flotilla v0.5.0  
**Assigned:** clau  
**Branch:** task/fwxfhcprzb6g2oc

---

## Goal

Extend `create-flotilla` so users can supply a custom profile pack at install time via
`--profile-dir` or `--profile-zip`, with the built-in `default-engineering` profile as
the fallback when neither flag is given.

---

## Dependency

V05-PROFILE-001 delivered the `profiles/default-engineering/` profile pack. This ticket
builds the installer hooks that consume it and any user-supplied profile.

---

## What Was Done

### 1. `package/lib/profile-validator.mjs` (new file)
Extracted and hardened profile validation logic into a standalone library:
- `isSafeRelativePath` — guards against path traversal, absolute paths, symlinks
- `isAllowedProfilePath` — whitelist of instruction/config destinations (matches spec)
- `isProfileExtensionPath` — allows `extensions/` subdirectory for manual-review files
- `isProfileDocumentationOnlyPath` — README.md is silently skipped during overlay
- `walkProfileDirectory` — safe recursive tree walk with symlink + escape detection
- `validateProfileDirectory` — full validation: existence, required files, JSON parse check
- `assertSafeZipEntries` — pre-flight zip listing to reject unsafe paths before extraction
- Exports `REQUIRED_PROFILE_FILES` and `OPTIONAL_PROFILE_FILES` constants

### 2. `package/bin/create-flotilla.mjs` (modified)
- Imports validation functions from `../lib/profile-validator.mjs`
- Removed inline `isAllowedProfilePath` and `walkDirectory` (now in validator)
- `resolveProfile`: uses `validateProfileDirectory` for all three profile sources
  (custom dir, custom zip, built-in default) — consistent, testable error messages
- `unzipProfile`: calls `assertSafeZipEntries` before extracting zip to temp dir
- `applyProfileOverlay`: uses `walkProfileDirectory` (symlink-safe), reports extension files
- `printNextSteps`: shows extension file count if any manual-review files exist
- `hasProfileFiles`: delegates to `validateProfileDirectory` (safe fallback for `findProfileRoot`)

### 3. Zip support decision
Zip support is **included** (not deferred). The `--profile-zip <path>` flag works:
- Lists zip entries via `unzip -Z1` (unix) or PowerShell `ZipFile` (windows) before extracting
- Rejects any unsafe paths in the zip before touching the filesystem
- Extracts to a temp dir, finds the profile root (handles top-level wrapping dirs), overlays,
  then cleans up the temp dir in `finally`.

---

## Acceptance Criteria — Status

| Criterion | Status |
|---|---|
| Installer without profile args uses default profile | ✅ `resolveProfile` falls back to `DEFAULT_PROFILE_DIR` |
| `--profile-dir` installs the provided profile | ✅ validated + overlaid |
| Zip support works | ✅ `--profile-zip` with safe entry check + temp-dir extraction |
| Invalid profile paths fail with useful message | ✅ `validateProfileDirectory` throws descriptive errors |
| Clear output showing which profile was used | ✅ `Profile: <label>` + file count in `printNextSteps` |

---

## Tests

Smoke tests in `package/tools/smoke-profile-install.mjs` cover all four acceptance criteria:
- PASS default built-in profile install
- PASS custom `--profile-dir` install
- PASS invalid profile rejection
- PASS custom `--profile-zip` install

Run: `node package/tools/smoke-profile-install.mjs`
