#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.join(__dirname, "..");
const DEFAULT_PROFILE_DIR = path.join(PACKAGE_ROOT, "profiles", "default-engineering");

const COPY_DIRECTORIES = [
  "blueprint",
  "dashboard",
  "data",
  "profiles",
  "scripts",
  "server",
];

const COPY_FILES = [
  "LICENSE",
  "COMPLIANCE.md",
  "INSTALL.md",
  "README.md",
];

function log(message) {
  process.stdout.write(`${message}${os.EOL}`);
}

function fail(message) {
  process.stderr.write(`${message}${os.EOL}`);
  process.exit(1);
}

function printHelp() {
  log("Usage: create-flotilla [target-dir] [options]");
  log("");
  log("Options:");
  log("  --profile-dir <path>  Overlay instruction/config files from a local profile directory");
  log("  --profile-zip <path>  Overlay instruction/config files from a local zip profile pack");
  log("  --install             Run npm install in the generated project");
  log("  --skip-git            Skip git init");
  log("  -h, --help            Show this help");
}

function parseArgs(argv) {
  const options = {
    projectName: "",
    dir: "",
    skipGit: false,
    install: false,
    profileDir: "",
    profileZip: "",
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg) continue;
    if (arg === "-h" || arg === "--help") {
      printHelp();
      process.exit(0);
    }
    if (arg === "--skip-git") {
      options.skipGit = true;
      continue;
    }
    if (arg === "--install") {
      options.install = true;
      continue;
    }
    if (arg === "--profile-dir" || arg === "--profile-zip") {
      const value = argv[i + 1];
      if (!value || value.startsWith("--")) {
        fail(`${arg} requires a path.`);
      }
      if (arg === "--profile-dir") {
        options.profileDir = value;
      } else {
        options.profileZip = value;
      }
      i += 1;
      continue;
    }
    if (arg.startsWith("--")) {
      fail(`Unknown option: ${arg}`);
    }
    if (!options.dir) {
      options.dir = arg;
      options.projectName = path.basename(arg);
      continue;
    }
    fail(`Unexpected argument: ${arg}`);
  }

  if (!options.dir) {
    options.dir = "agentfleet-app";
    options.projectName = "agentfleet-app";
  }

  if (options.profileDir && options.profileZip) {
    fail("Use either --profile-dir or --profile-zip, not both.");
  }

  return options;
}

function ensureEmptyTarget(targetPath) {
  if (!fs.existsSync(targetPath)) {
    fs.mkdirSync(targetPath, { recursive: true });
    return;
  }
  const entries = fs.readdirSync(targetPath);
  if (entries.length > 0) {
    fail(`Target directory is not empty: ${targetPath}`);
  }
}

function copyFile(sourcePath, targetPath) {
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
  fs.copyFileSync(sourcePath, targetPath);
}

function copyDirectory(sourceDir, targetDir) {
  fs.mkdirSync(targetDir, { recursive: true });
  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    const sourcePath = path.join(sourceDir, entry.name);
    const targetPath = path.join(targetDir, entry.name);
    if (entry.isDirectory()) {
      copyDirectory(sourcePath, targetPath);
    } else {
      copyFile(sourcePath, targetPath);
    }
  }
}

function isAllowedProfilePath(relativePath) {
  const clean = relativePath.replace(/\\/g, "/");
  if (!clean || clean.startsWith("/") || clean.includes("../") || clean === "..") return false;
  if (clean === ".gitignore" || clean === "gitignore.template") return true;
  if (["AGENTS.md", "CLAUDE.md", "GEMINI.md", "GEMMA.md", "MISTRAL.md", "MISSION_CONTROL.md", "ARCHITECTURE.md"].includes(clean)) return true;
  if (clean === "AGENTS/RULES.md" || clean === "AGENTS/KEYVAULT.md") return true;
  if (clean === "AGENTS/MESSAGES/inbox.json" || clean === "AGENTS/LESSONS/ledger.json") return true;
  if (clean === "standups/index.json" || clean === "standups/README.md") return true;
  if (/^AGENTS\/CONFIG\/[A-Za-z0-9._-]+\.json$/.test(clean)) return true;
  if (/^AGENTS\/CONTEXT\/[A-Za-z0-9._/-]+\.md$/.test(clean) && !clean.includes("..")) return true;
  return false;
}

function hasProfileFiles(profileDir) {
  if (!fs.existsSync(profileDir) || !fs.statSync(profileDir).isDirectory()) return false;
  return walkDirectory(profileDir).some(filePath => isAllowedProfilePath(path.relative(profileDir, filePath)));
}

function walkDirectory(rootPath) {
  const entries = [];
  for (const dirent of fs.readdirSync(rootPath, { withFileTypes: true })) {
    const fullPath = path.join(rootPath, dirent.name);
    if (dirent.isSymbolicLink()) {
      fail(`Profile pack contains a symbolic link, which is not allowed: ${path.relative(rootPath, fullPath)}`);
    }
    if (dirent.isDirectory()) {
      entries.push(...walkDirectory(fullPath));
    } else if (dirent.isFile()) {
      entries.push(fullPath);
    }
  }
  return entries;
}

function findProfileRoot(candidateDir) {
  if (hasProfileFiles(candidateDir)) return candidateDir;
  const dirs = fs.readdirSync(candidateDir, { withFileTypes: true }).filter(entry => entry.isDirectory());
  if (dirs.length === 1) {
    const nested = path.join(candidateDir, dirs[0].name);
    if (hasProfileFiles(nested)) return nested;
  }
  return "";
}

function unzipProfile(zipPath) {
  const resolved = path.resolve(zipPath);
  if (!fs.existsSync(resolved)) {
    fail(`Profile zip does not exist: ${resolved}`);
  }
  if (!fs.statSync(resolved).isFile()) {
    fail(`Profile zip is not a file: ${resolved}`);
  }

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "flotilla-profile-"));
  const unzip = process.platform === "win32"
    ? spawnSync("powershell.exe", ["-NoProfile", "-Command", "Expand-Archive", "-LiteralPath", resolved, "-DestinationPath", tempDir], { encoding: "utf8", windowsHide: true })
    : spawnSync("unzip", ["-q", resolved, "-d", tempDir], { encoding: "utf8", windowsHide: true });

  if (unzip.error || unzip.status !== 0) {
    fs.rmSync(tempDir, { recursive: true, force: true });
    const detail = unzip.error?.message || unzip.stderr || unzip.stdout || "zip extraction failed";
    fail(`Could not extract profile zip ${resolved}: ${detail.trim()}`);
  }

  const profileRoot = findProfileRoot(tempDir);
  if (!profileRoot) {
    fs.rmSync(tempDir, { recursive: true, force: true });
    fail(`Profile zip does not contain supported instruction/config files: ${resolved}`);
  }
  return { profileRoot, tempDir };
}

function resolveProfile(options) {
  if (options.profileDir) {
    const profileRoot = path.resolve(options.profileDir);
    if (!fs.existsSync(profileRoot)) {
      fail(`Profile directory does not exist: ${profileRoot}`);
    }
    if (!fs.statSync(profileRoot).isDirectory()) {
      fail(`Profile directory is not a directory: ${profileRoot}`);
    }
    if (!hasProfileFiles(profileRoot)) {
      fail(`Profile directory does not contain supported instruction/config files: ${profileRoot}`);
    }
    return { profileRoot, label: profileRoot, tempDir: "" };
  }

  if (options.profileZip) {
    const extracted = unzipProfile(options.profileZip);
    return { ...extracted, label: path.resolve(options.profileZip) };
  }

  if (!hasProfileFiles(DEFAULT_PROFILE_DIR)) {
    fail(`Built-in default profile is missing or invalid: ${DEFAULT_PROFILE_DIR}`);
  }
  return { profileRoot: DEFAULT_PROFILE_DIR, label: "default-engineering (built-in)", tempDir: "" };
}

function applyProfileOverlay(profileRoot, targetPath) {
  const filesWritten = [];
  const skipped = [];

  for (const sourcePath of walkDirectory(profileRoot)) {
    const relativePath = path.relative(profileRoot, sourcePath).replace(/\\/g, "/");
    if (!isAllowedProfilePath(relativePath)) {
      skipped.push(relativePath);
      continue;
    }

    const targetRelativePath = relativePath === "gitignore.template" ? ".gitignore" : relativePath;
    copyFile(sourcePath, path.join(targetPath, targetRelativePath));
    filesWritten.push(targetRelativePath);
  }

  if (!filesWritten.length) {
    fail(`Profile pack did not overlay any supported files: ${profileRoot}`);
  }

  return {
    filesWritten: Array.from(new Set(filesWritten)).sort(),
    skipped: skipped.sort(),
  };
}

function writeProjectPackageJson(targetPath, projectName) {
  const packageJson = {
    name: projectName.toLowerCase().replace(/[^a-z0-9-_]/g, "-"),
    version: "0.1.0",
    private: true,
    type: "module",
    description: "Flotilla workspace generated by create-flotilla",
    scripts: {
      start: "node ./server/fleet-server.mjs",
      dev: "node --watch ./server/fleet-server.mjs",
      doctor: "node ./scripts/doctor.mjs"
    },
    engines: {
      node: ">=18.0.0"
    }
  };
  fs.writeFileSync(path.join(targetPath, "package.json"), `${JSON.stringify(packageJson, null, 2)}${os.EOL}`);
}

function writeGitignore(targetPath) {
  const content = [
    "node_modules/",
    "__pycache__/",
    "*.pyc",
    ".env",
    ".env.*",
    "*.pickle",
    ".DS_Store",
  ].join(os.EOL);
  fs.writeFileSync(path.join(targetPath, ".gitignore"), `${content}${os.EOL}`);
}

function writeDoctorScript(targetPath) {
  const content = [
    'import { runDoctor, readJson, getDefaultFleetMeta, normalizeFleetMeta } from "../server/setup-lib.mjs";',
    'import path from "node:path";',
    'import { fileURLToPath } from "node:url";',
    "",
    "const __dirname = path.dirname(fileURLToPath(import.meta.url));",
    'const metaPath = path.join(__dirname, "..", "data", "config", "fleet_meta.json");',
    "const meta = normalizeFleetMeta(readJson(metaPath, getDefaultFleetMeta()));",
    "const result = runDoctor(meta);",
    "console.log(JSON.stringify(result, null, 2));",
    "process.exit(result.ok ? 0 : 1);",
    "",
  ].join(os.EOL);
  fs.writeFileSync(path.join(targetPath, "scripts", "doctor.mjs"), content);
}

function maybeInitGit(targetPath) {
  const gitDir = path.join(targetPath, ".git");
  if (fs.existsSync(gitDir)) return;
  spawnSync("git", ["init"], { cwd: targetPath, stdio: "ignore", windowsHide: true });
}

function maybeInstall(targetPath) {
  const npm = process.platform === "win32" ? "npm.cmd" : "npm";
  const result = spawnSync(npm, ["install"], {
    cwd: targetPath,
    stdio: "inherit",
    windowsHide: true,
  });
  if (result.status !== 0) {
    fail("npm install failed.");
  }
}

function printNextSteps(targetPath, options, profileResult) {
  const relative = path.relative(process.cwd(), targetPath) || ".";
  log("");
  log("Flotilla scaffold created.");
  log(`Profile: ${profileResult.label}`);
  log(`Profile files overlaid: ${profileResult.filesWritten.length}`);
  if (profileResult.skipped.length) {
    log(`Profile files skipped outside instruction/config destinations: ${profileResult.skipped.length}`);
  }
  log("");
  log("Next steps:");
  log(`  cd ${relative}`);
  if (!options.install) {
    log("  npm install");
  }
  log("  npm start");
  log("  open http://localhost:8787/setup/");
  log("");
  log("The installer leaves onboarding to /setup/ so the wizard stays rerunnable.");
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  const profile = resolveProfile(options);
  const targetPath = path.resolve(process.cwd(), options.dir);
  let profileResult = null;
  try {
    ensureEmptyTarget(targetPath);

    for (const dir of COPY_DIRECTORIES) {
      copyDirectory(path.join(PACKAGE_ROOT, dir), path.join(targetPath, dir));
    }

    for (const file of COPY_FILES) {
      copyFile(path.join(PACKAGE_ROOT, file), path.join(targetPath, file));
    }

    writeProjectPackageJson(targetPath, options.projectName);
    writeGitignore(targetPath);
    writeDoctorScript(targetPath);
    profileResult = {
      label: profile.label,
      ...applyProfileOverlay(profile.profileRoot, targetPath),
    };

    if (!options.skipGit) {
      maybeInitGit(targetPath);
    }

    if (options.install) {
      maybeInstall(targetPath);
    }

    printNextSteps(targetPath, options, profileResult);
  } finally {
    if (profile.tempDir) {
      fs.rmSync(profile.tempDir, { recursive: true, force: true });
    }
  }
}

main();
