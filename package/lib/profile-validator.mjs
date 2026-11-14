import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

export const REQUIRED_PROFILE_FILES = [
  "MISSION_CONTROL.md",
  "AGENTS.md",
  "AGENTS/RULES.md",
  "AGENTS/KEYVAULT.md",
  "AGENTS/CONFIG/fleet_meta.json",
  "AGENTS/MESSAGES/inbox.json",
  "AGENTS/LESSONS/ledger.json",
  "standups/index.json",
];

export const OPTIONAL_PROFILE_FILES = [
  ".gitignore",
  "gitignore.template",
  "ARCHITECTURE.md",
  "CLAUDE.md",
  "GEMINI.md",
  "GEMMA.md",
  "MISTRAL.md",
  "README.md",
  "standups/README.md",
];

const ROOT_MARKDOWN_FILES = new Set([
  "AGENTS.md",
  "ARCHITECTURE.md",
  "CLAUDE.md",
  "GEMINI.md",
  "GEMMA.md",
  "MISSION_CONTROL.md",
  "MISTRAL.md",
]);

const DOCUMENTATION_ONLY_FILES = new Set(["README.md"]);

function normalizeRelativePath(relativePath) {
  return relativePath.replace(/\\/g, "/");
}

export function isSafeRelativePath(relativePath) {
  const clean = normalizeRelativePath(relativePath);
  if (!clean || clean === "." || clean.startsWith("/") || clean.startsWith("../")) return false;
  if (clean === ".." || clean.includes("/../") || clean.endsWith("/..")) return false;
  if (/^[A-Za-z]:\//.test(clean)) return false;
  if (path.isAbsolute(clean)) return false;
  return true;
}

export function isAllowedProfilePath(relativePath) {
  const clean = normalizeRelativePath(relativePath);
  if (!isSafeRelativePath(clean)) return false;
  if (clean === ".gitignore" || clean === "gitignore.template") return true;
  if (ROOT_MARKDOWN_FILES.has(clean)) return true;
  if (clean === "AGENTS/RULES.md" || clean === "AGENTS/KEYVAULT.md") return true;
  if (clean === "AGENTS/MESSAGES/inbox.json" || clean === "AGENTS/LESSONS/ledger.json") return true;
  if (clean === "standups/index.json" || clean === "standups/README.md") return true;
  if (/^AGENTS\/CONFIG\/[A-Za-z0-9._-]+\.json$/.test(clean)) return true;
  if (/^AGENTS\/CONTEXT\/[A-Za-z0-9._/-]+\.md$/.test(clean)) return true;
  return false;
}

export function isProfileExtensionPath(relativePath) {
  const clean = normalizeRelativePath(relativePath);
  return isSafeRelativePath(clean) && /^extensions\/[A-Za-z0-9._/-]+$/.test(clean);
}

export function isProfileDocumentationOnlyPath(relativePath) {
  const clean = normalizeRelativePath(relativePath);
  return isSafeRelativePath(clean) && DOCUMENTATION_ONLY_FILES.has(clean);
}

export function walkProfileDirectory(rootPath) {
  const rootRealPath = fs.realpathSync(rootPath);
  const entries = [];

  function visit(currentPath) {
    for (const dirent of fs.readdirSync(currentPath, { withFileTypes: true })) {
      const fullPath = path.join(currentPath, dirent.name);
      const relativePath = normalizeRelativePath(path.relative(rootPath, fullPath));
      if (!isSafeRelativePath(relativePath)) {
        throw new Error(`Profile pack contains an unsafe path: ${relativePath}`);
      }
      if (dirent.isSymbolicLink()) {
        throw new Error(`Profile pack contains a symbolic link, which is not allowed: ${relativePath}`);
      }
      const resolvedPath = fs.realpathSync(fullPath);
      if (resolvedPath !== rootRealPath && !resolvedPath.startsWith(`${rootRealPath}${path.sep}`)) {
        throw new Error(`Profile pack path escapes the profile root: ${relativePath}`);
      }
      if (dirent.isDirectory()) {
        visit(fullPath);
      } else if (dirent.isFile()) {
        entries.push(fullPath);
      }
    }
  }

  visit(rootPath);
  return entries;
}

export function validateProfileDirectory(profileRoot) {
  const resolvedRoot = path.resolve(profileRoot);
  if (!fs.existsSync(resolvedRoot)) {
    throw new Error(`Profile directory does not exist: ${resolvedRoot}`);
  }
  if (!fs.statSync(resolvedRoot).isDirectory()) {
    throw new Error(`Profile directory is not a directory: ${resolvedRoot}`);
  }

  const allowedFiles = [];
  const documentationFiles = [];
  const extensionFiles = [];
  const unknownFiles = [];
  const allFiles = walkProfileDirectory(resolvedRoot);
  const present = new Set();

  for (const sourcePath of allFiles) {
    const relativePath = normalizeRelativePath(path.relative(resolvedRoot, sourcePath));
    if (!isSafeRelativePath(relativePath)) {
      throw new Error(`Profile pack contains an unsafe path: ${relativePath}`);
    }
    if (isAllowedProfilePath(relativePath)) {
      allowedFiles.push(sourcePath);
      present.add(relativePath === "gitignore.template" ? ".gitignore" : relativePath);
      if (relativePath.endsWith(".json")) {
        try {
          JSON.parse(fs.readFileSync(sourcePath, "utf8"));
        } catch (error) {
          throw new Error(`Invalid JSON in profile file ${relativePath}: ${error.message}`);
        }
      }
    } else if (isProfileExtensionPath(relativePath)) {
      extensionFiles.push(relativePath);
    } else if (isProfileDocumentationOnlyPath(relativePath)) {
      documentationFiles.push(relativePath);
    } else {
      unknownFiles.push(relativePath);
    }
  }

  const missing = REQUIRED_PROFILE_FILES.filter(relativePath => !present.has(relativePath));
  if (missing.length) {
    throw new Error(`Profile pack is missing required file(s): ${missing.join(", ")}`);
  }

  return {
    profileRoot: resolvedRoot,
    allowedFiles: allowedFiles.sort(),
    documentationFiles: documentationFiles.sort(),
    extensionFiles: extensionFiles.sort(),
    unknownFiles: unknownFiles.sort(),
    requiredFiles: [...REQUIRED_PROFILE_FILES],
    optionalFiles: [...OPTIONAL_PROFILE_FILES],
  };
}

export function profileHasRequiredFiles(profileRoot) {
  try {
    validateProfileDirectory(profileRoot);
    return true;
  } catch {
    return false;
  }
}

export function assertSafeZipEntries(zipPath) {
  const resolvedZipPath = path.resolve(zipPath);
  const unzip = process.platform === "win32"
    ? spawnSync("powershell.exe", ["-NoProfile", "-Command", `Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::OpenRead('${resolvedZipPath.replace(/'/g, "''")}').Entries | ForEach-Object { $_.FullName }`], { encoding: "utf8", windowsHide: true })
    : spawnSync("unzip", ["-Z1", resolvedZipPath], { encoding: "utf8", windowsHide: true });

  if (unzip.error || unzip.status !== 0) {
    const detail = unzip.error?.message || unzip.stderr || unzip.stdout || "zip listing failed";
    throw new Error(`Could not inspect profile zip ${resolvedZipPath}: ${detail.trim()}`);
  }

  for (const rawEntry of (unzip.stdout || "").split(/\r?\n/)) {
    const entry = rawEntry.trim();
    if (!entry || entry.endsWith("/")) continue;
    if (!isSafeRelativePath(entry)) {
      throw new Error(`Profile zip contains an unsafe path: ${entry}`);
    }
  }
}
