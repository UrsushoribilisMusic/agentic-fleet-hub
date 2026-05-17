#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.join(__dirname, "..");
const SCAFFOLDER = path.join(PACKAGE_ROOT, "bin", "create-flotilla.mjs");
const FIXTURE_ROOT = path.join(PACKAGE_ROOT, "test-fixtures", "profiles");
const REQUIRED_INSTALL_FILES = [
  "MISSION_CONTROL.md",
  "AGENTS.md",
  "AGENTS/RULES.md",
  "AGENTS/KEYVAULT.md",
  "AGENTS/CONFIG/fleet_meta.json",
  "AGENTS/MESSAGES/inbox.json",
  "AGENTS/LESSONS/ledger.json",
  "standups/index.json",
];

function pass(message) {
  console.log(`PASS ${message}`);
}

function fail(message) {
  throw new Error(message);
}

function assert(condition, message) {
  if (!condition) fail(message);
}

function run(command, args, options = {}) {
  return spawnSync(command, args, {
    encoding: "utf8",
    windowsHide: true,
    ...options,
  });
}

function runRequired(command, args, options = {}) {
  const result = run(command, args, options);
  if (result.error) throw result.error;
  if (result.status !== 0) {
    fail((result.stderr || result.stdout || `${command} failed`).trim());
  }
  return result;
}

function assertInstructionFiles(targetPath) {
  for (const relativePath of REQUIRED_INSTALL_FILES) {
    assert(fs.existsSync(path.join(targetPath, relativePath)), `missing ${relativePath}`);
  }
}

function assertJsonParses(targetPath, relativePath) {
  JSON.parse(fs.readFileSync(path.join(targetPath, relativePath), "utf8"));
}

function verifyDefaultInstall(tempRoot) {
  const targetPath = path.join(tempRoot, "default-profile-fleet");
  const result = runRequired(process.execPath, [SCAFFOLDER, targetPath, "--skip-git"]);
  assert(result.stdout.includes("Profile: default-engineering (built-in)"), "default install did not report built-in profile");
  assertInstructionFiles(targetPath);
  assertJsonParses(targetPath, "AGENTS/CONFIG/fleet_meta.json");
  assert(fs.readFileSync(path.join(targetPath, "MISSION_CONTROL.md"), "utf8").includes("default-engineering"), "default profile did not overlay mission control");
  assert(fs.readFileSync(path.join(targetPath, "AGENTS/RULES.md"), "utf8").includes("Heartbeat Protocol"), "default profile did not overlay team rules");
  pass("default built-in profile install");
}

function verifyCustomProfileInstall(tempRoot) {
  const targetPath = path.join(tempRoot, "custom-profile-fleet");
  const profilePath = path.join(FIXTURE_ROOT, "valid-minimal");
  const result = runRequired(process.execPath, [SCAFFOLDER, targetPath, "--skip-git", "--profile-dir", profilePath]);
  assert(result.stdout.includes(`Profile: ${profilePath}`), "custom profile install did not report profile path");
  assertInstructionFiles(targetPath);
  assertJsonParses(targetPath, "AGENTS/CONFIG/fleet_meta.json");
  assert(fs.readFileSync(path.join(targetPath, "AGENTS/RULES.md"), "utf8").includes("Test Rules"), "custom profile did not overlay AGENTS/RULES.md");
  assert(fs.readFileSync(path.join(targetPath, "MISSION_CONTROL.md"), "utf8").includes("Test Mission Control"), "custom profile did not overlay MISSION_CONTROL.md");
  assert(!fs.existsSync(path.join(targetPath, "extensions", "README.md")), "profile extensions were copied into the install tree");
  pass("custom --profile-dir install");
}

function verifyInvalidProfileRejection(tempRoot) {
  const targetPath = path.join(tempRoot, "invalid-profile-fleet");
  const profilePath = path.join(FIXTURE_ROOT, "missing-required");
  const result = run(process.execPath, [SCAFFOLDER, targetPath, "--skip-git", "--profile-dir", profilePath]);
  assert(result.status !== 0, "invalid profile unexpectedly installed");
  assert((result.stderr || "").includes("missing required file(s)"), "invalid profile error did not explain missing required files");
  assert(!fs.existsSync(targetPath), "invalid profile left a partial install target");
  pass("invalid profile rejection");
}

function verifyZipProfileInstall(tempRoot) {
  const profilePath = path.join(FIXTURE_ROOT, "valid-minimal");
  const zipPath = path.join(tempRoot, "valid-minimal-profile.zip");
  const targetPath = path.join(tempRoot, "zip-profile-fleet");
  runRequired("zip", ["-qr", zipPath, "."], { cwd: profilePath });
  const result = runRequired(process.execPath, [SCAFFOLDER, targetPath, "--skip-git", "--profile-zip", zipPath]);
  assert(result.stdout.includes(`Profile: ${zipPath}`), "zip profile install did not report zip path");
  assertInstructionFiles(targetPath);
  assert(fs.readFileSync(path.join(targetPath, "AGENTS/RULES.md"), "utf8").includes("Test Rules"), "zip profile did not overlay AGENTS/RULES.md");
  pass("custom --profile-zip install");
}

function main() {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "flotilla-profile-smoke-"));
  console.log("Profile install smoke tests");
  console.log(`Temp root: ${tempRoot}`);
  try {
    verifyDefaultInstall(tempRoot);
    verifyCustomProfileInstall(tempRoot);
    verifyInvalidProfileRejection(tempRoot);
    verifyZipProfileInstall(tempRoot);
    console.log("Profile install smoke tests passed");
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

main();
