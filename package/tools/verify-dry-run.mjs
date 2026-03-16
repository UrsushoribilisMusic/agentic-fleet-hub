#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.join(__dirname, "..");
const SCAFFOLDER = path.join(PACKAGE_ROOT, "bin", "create-flotilla.mjs");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    windowsHide: true,
    ...options,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error((result.stderr || result.stdout || `${command} failed`).trim());
  }
  return (result.stdout || "").trim();
}

function verifyDashboard(targetPath) {
  const html = fs.readFileSync(path.join(targetPath, "dashboard", "engineering", "index.html"), "utf8");
  const mainJs = fs.readFileSync(path.join(targetPath, "dashboard", "engineering", "assets", "main.js"), "utf8");
  const styleCss = fs.readFileSync(path.join(targetPath, "dashboard", "engineering", "assets", "style.css"), "utf8");

  const requiredSections = [
    'id="section-team"',
    'id="section-projects"',
    'id="section-kanban"',
    'id="section-rules"',
    'id="section-memory"',
    'id="section-standups"',
    'id="section-inbox"',
    'id="section-users"',
  ];

  for (const marker of requiredSections) {
    assert(html.includes(marker), `engineering/index.html missing ${marker}`);
  }

  assert(html.includes('id="theme-toggle-btn"'), "engineering/index.html missing theme toggle button");
  assert(html.includes('onclick="openAgentModal()"'), "engineering/index.html missing Add Agent action");
  assert(html.includes('assets/main.js'), "engineering/index.html missing main.js asset reference");
  assert(html.includes('assets/style.css'), "engineering/index.html missing style.css asset reference");

  assert(mainJs.includes("window.openAgentModal"), "engineering main.js missing openAgentModal");
  assert(mainJs.includes("document.getElementById('agent-form').onsubmit"), "engineering main.js missing Add Agent submit handler");
  assert(mainJs.includes("theme-toggle-btn"), "engineering main.js missing theme toggle wiring");
  assert(styleCss.includes('[data-theme="dark"]'), "engineering style.css missing dark theme support");
}

async function main() {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "flotilla-dry-run-"));
  const targetPath = path.join(tempRoot, "smoke-fleet");

  try {
    run(process.execPath, [SCAFFOLDER, targetPath]);

    const expectedFiles = [
      "package.json",
      "server/fleet-server.mjs",
      "server/setup-lib.mjs",
      "scripts/doctor.mjs",
      "scripts/dispatcher.py",
      "scripts/telegram_bridge.py",
      "scripts/github_sync.py",
      "scripts/fleet.github.plist",
      "scripts/fleet_push.py",
      "scripts/fleet.push.plist",
      "scripts/fleet.pocketbase.plist",
      "dashboard/setup/index.html",
      "dashboard/configure/index.html",
      "dashboard/engineering/index.html",
      "dashboard/engineering/assets/main.js",
      "dashboard/engineering/assets/style.css",
      "data/config/fleet_meta.json",
    ];

    for (const relativePath of expectedFiles) {
      assert(fs.existsSync(path.join(targetPath, relativePath)), `Scaffold missing ${relativePath}`);
    }

    const setupLib = await import(pathToFileURL(path.join(targetPath, "server", "setup-lib.mjs")).href);
    let meta = setupLib.buildSetupPayload(setupLib.getDefaultFleetMeta(), {
      org_name: "Smoke Fleet",
      deployment_scenario: "hybrid",
      repo_path: targetPath,
      repo_url: "https://github.com/acme/smoke-fleet",
      kanban_url: "https://github.com/orgs/acme/projects/1",
      crm_url: "https://example.com/crm",
      vault_provider: "infisical",
      vault_region: "EU",
      telegram_enabled: true,
      telegram_chat_id: "-1001234567890",
      openclaw_enabled: true,
      openclaw_gateway_url: "http://localhost:18789",
      github_sync_enabled: true,
      github_sync_repo: "acme/smoke-fleet",
      selected_agents: [
        { id: "claude_code", name: "Clau" },
        { id: "gemini_cli", name: "Gem" },
        { id: "codex", name: "Codi" },
      ],
    });

    const bootstrap = setupLib.writeBootstrapFiles(meta, targetPath);
    meta = setupLib.updateBootstrapMetadata(meta, bootstrap);
    setupLib.writeJson(path.join(targetPath, "data", "config", "fleet_meta.json"), meta);

    const doctorRaw = run(process.execPath, [path.join(targetPath, "scripts", "doctor.mjs")], {
      cwd: targetPath,
      env: {
        ...process.env,
        TELEGRAM_TOKEN: "dry-run-telegram-token",
        GITHUB_TOKEN: "dry-run-github-token",
        FLEET_SYNC_TOKEN: "dry-run-fleet-sync-token",
      },
    });
    const doctor = JSON.parse(doctorRaw);
    assert(doctor.ok, `Generated doctor failed: ${doctor.issues.join(" | ")}`);

    run("git", ["rev-parse", "--is-inside-work-tree"], { cwd: targetPath });
    verifyDashboard(targetPath);

    console.log("verify:dry-run passed");
    console.log(`Scaffolded: ${targetPath}`);
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(`verify:dry-run failed: ${error.message}`);
  process.exit(1);
});
