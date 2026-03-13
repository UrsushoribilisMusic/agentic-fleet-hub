import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.join(__dirname, "..");
const BLUEPRINT_ROOT = path.join(PACKAGE_ROOT, "blueprint");
const DEFAULT_GROWTH_META_PATH = path.join(PACKAGE_ROOT, "data", "config", "growth_meta.json");

const TEXT_FILE_EXTENSIONS = new Set([".md", ".json", ".txt", ".py", ".ps1", ".sh", ".yml", ".yaml", ".js", ".mjs"]);

const AGENT_PRESETS = {
  claude_code: {
    id: "claude_code",
    label: "Claude Code",
    defaultName: "Clau",
    runtime: "Hybrid",
    roleTitle: "Senior Logic and Implementation",
    roleDesc: "Owns high-precision implementation work, refactors risky code paths, and closes complex tickets cleanly.",
    skills: ["Implementation", "Refactoring", "Debugging"],
    memoryLinkSuffix: "AGENTS/RULES.md",
    bootstrapInstruction: "Claude Code reads CLAUDE.md automatically.",
  },
  gemini_cli: {
    id: "gemini_cli",
    label: "Gemini CLI",
    defaultName: "Gem",
    runtime: "Cloud",
    roleTitle: "Context and Infrastructure Architect",
    roleDesc: "Handles large-context synthesis, platform stability, and cross-project documentation flow.",
    skills: ["Context Synthesis", "Infrastructure", "Documentation"],
    memoryLinkSuffix: "AGENTS/RULES.md",
    bootstrapInstruction: "Gemini CLI reads GEMINI.md automatically.",
  },
  codex: {
    id: "codex",
    label: "Codex",
    defaultName: "Codi",
    runtime: "Cloud Runner",
    roleTitle: "QA and Delivery Runner",
    roleDesc: "Pushes feature throughput, validates changes, and keeps the delivery loop moving.",
    skills: ["API Prototyping", "QA Automation", "Delivery"],
    memoryLinkSuffix: "AGENTS/RULES.md",
    bootstrapInstruction: "Codex reads AGENTS.md automatically.",
  },
  mistral_vibe: {
    id: "mistral_vibe",
    label: "Mistral Vibe",
    defaultName: "Misty",
    runtime: "Hybrid",
    roleTitle: "Secondary Operator and Exploratory Support",
    roleDesc: "Adds parallel implementation capacity and exploratory reasoning for adjacent tickets.",
    skills: ["Parallel Execution", "Exploration", "Support"],
    memoryLinkSuffix: "AGENTS/RULES.md",
    bootstrapInstruction: "In the first prompt, paste: Read AGENTS.md before doing anything else.",
  },
};

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function isoNow() {
  return new Date().toISOString();
}

function normalizeString(value, fallback = "") {
  return typeof value === "string" ? value.trim() : fallback;
}

function slugify(value) {
  return normalizeString(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function fileExists(targetPath) {
  try {
    return fs.existsSync(targetPath);
  } catch {
    return false;
  }
}

export function readJson(filePath, fallback) {
  try {
    if (!fileExists(filePath)) return deepClone(fallback);
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return deepClone(fallback);
  }
}

export function writeJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

export function getAgentCatalog() {
  return Object.values(AGENT_PRESETS).map(agent => ({
    id: agent.id,
    label: agent.label,
    default_name: agent.defaultName,
    bootstrap_instruction: agent.bootstrapInstruction,
  }));
}

function toRepoBlobUrl(repoUrl, suffix) {
  const clean = normalizeString(repoUrl);
  if (!clean) return "#";
  const trimmed = clean.replace(/\/+$/, "");
  return `${trimmed}/blob/master/${suffix}`;
}

function buildTeam(selectedAgents, repoUrl) {
  if (!selectedAgents.length) return [];
  return selectedAgents.map(agent => {
    const preset = AGENT_PRESETS[agent.id];
    return {
      name: agent.name,
      avatar: preset.id === "claude_code" ? "AI" : preset.id === "gemini_cli" ? "GM" : preset.id === "codex" ? "CX" : "MV",
      roleTitle: preset.roleTitle,
      roleDesc: preset.roleDesc,
      skills: preset.skills,
      runtime: preset.runtime,
      memoryLink: toRepoBlobUrl(repoUrl, preset.memoryLinkSuffix),
    };
  });
}

function buildProjects(orgName, repoUrl, kanbanUrl, crmUrl) {
  const docsUrl = repoUrl ? `${repoUrl.replace(/\/+$/, "")}/blob/master/MISSION_CONTROL.md` : "#";
  return [
    {
      title: `${orgName} Fleet`,
      owners: "Coordinator",
      summary: "Primary coordination workspace for the multi-agent team, including rules, standups, and shared operational memory.",
      docs: [docsUrl],
      kanban: kanbanUrl || repoUrl || "#",
      crmLink: crmUrl || undefined,
    },
  ];
}

function buildDemoTemplate(team, projects) {
  return {
    team: deepClone(team),
    projects: deepClone(projects),
  };
}

function buildGrowthTemplate(kanbanUrl, crmUrl) {
  const fallback = readJson(DEFAULT_GROWTH_META_PATH, { team: [], projects: [] });
  const growth = deepClone(fallback);
  growth.projects = (growth.projects || []).map(project => ({
    ...project,
    kanban: kanbanUrl || project.kanban || "#",
    crmLink: crmUrl || project.crmLink || "#",
    statsLink: project.statsLink || (crmUrl ? `${crmUrl.replace(/\/+$/, "")}?tab=calendar` : "#"),
  }));
  return growth;
}

function normalizeSelectedAgents(inputAgents) {
  const rawAgents = Array.isArray(inputAgents) ? inputAgents : [];
  const selected = [];
  for (const item of rawAgents) {
    const id = normalizeString(item?.id);
    const preset = AGENT_PRESETS[id];
    if (!preset) continue;
    if (selected.find(existing => existing.id === id)) continue;
    selected.push({
      id,
      label: preset.label,
      name: normalizeString(item?.name, preset.defaultName) || preset.defaultName,
    });
  }
  return selected;
}

export function getDefaultFleetMeta() {
  return {
    meta: {
      installation: {
        setup_completed: false,
        org_name: "AgentFleet",
        repo_path: "",
        repo_url: "",
        kanban_url: "",
        crm_url: "",
        vault: {
          provider: "infisical",
          region: "EU",
        },
        selected_agents: [
          { id: "claude_code", label: "Claude Code", name: "Clau" },
          { id: "gemini_cli", label: "Gemini CLI", name: "Gem" },
          { id: "codex", label: "Codex", name: "Codi" },
        ],
        bootstrap: {
          last_written_at: null,
          last_repo_path: "",
          files_written: [],
        },
        completed_at: null,
        updated_at: null,
      },
      templates: {
        demo: {
          team: [],
          projects: [],
        },
        growth: {
          team: [],
          projects: [],
        },
      },
    },
    team: [],
    projects: [],
  };
}

export function normalizeFleetMeta(inputMeta) {
  const fallback = getDefaultFleetMeta();
  const source = inputMeta && typeof inputMeta === "object" ? inputMeta : {};
  const installation = source.meta?.installation || {};
  const selectedAgents = normalizeSelectedAgents(installation.selected_agents?.length ? installation.selected_agents : fallback.meta.installation.selected_agents);
  const orgName = normalizeString(installation.org_name, fallback.meta.installation.org_name);
  const repoUrl = normalizeString(installation.repo_url);
  const kanbanUrl = normalizeString(installation.kanban_url);
  const crmUrl = normalizeString(installation.crm_url);
  const team = Array.isArray(source.team) && source.team.length ? source.team : buildTeam(selectedAgents, repoUrl);
  const projects = Array.isArray(source.projects) && source.projects.length ? source.projects : buildProjects(orgName, repoUrl, kanbanUrl, crmUrl);

  return {
    meta: {
      installation: {
        setup_completed: Boolean(installation.setup_completed),
        org_name: orgName,
        repo_path: normalizeString(installation.repo_path),
        repo_url: repoUrl,
        kanban_url: kanbanUrl,
        crm_url: crmUrl,
        vault: {
          provider: normalizeString(installation.vault?.provider, "infisical") || "infisical",
          region: normalizeString(installation.vault?.region, "EU") || "EU",
        },
        selected_agents: selectedAgents,
        bootstrap: {
          last_written_at: installation.bootstrap?.last_written_at || null,
          last_repo_path: normalizeString(installation.bootstrap?.last_repo_path),
          files_written: Array.isArray(installation.bootstrap?.files_written) ? installation.bootstrap.files_written : [],
        },
        completed_at: installation.completed_at || null,
        updated_at: installation.updated_at || null,
      },
      templates: {
        demo: source.meta?.templates?.demo || buildDemoTemplate(team, projects),
        growth: source.meta?.templates?.growth || buildGrowthTemplate(kanbanUrl, crmUrl),
      },
    },
    team,
    projects,
  };
}

export function buildSetupPayload(existingMeta, body) {
  const current = normalizeFleetMeta(existingMeta);
  const installation = current.meta.installation;
  const selectedAgents = normalizeSelectedAgents(body.selected_agents?.length ? body.selected_agents : installation.selected_agents);
  const orgName = normalizeString(body.org_name, installation.org_name);
  const repoPath = normalizeString(body.repo_path, installation.repo_path);
  const repoUrl = normalizeString(body.repo_url, installation.repo_url);
  const kanbanUrl = normalizeString(body.kanban_url, installation.kanban_url);
  const crmUrl = normalizeString(body.crm_url, installation.crm_url);
  const updatedAt = isoNow();
  const completedAt = installation.completed_at || updatedAt;
  const team = buildTeam(selectedAgents, repoUrl);
  const projects = buildProjects(orgName, repoUrl, kanbanUrl, crmUrl);

  return {
    meta: {
      installation: {
        setup_completed: true,
        org_name: orgName,
        repo_path: repoPath,
        repo_url: repoUrl,
        kanban_url: kanbanUrl,
        crm_url: crmUrl,
        vault: {
          provider: normalizeString(body.vault_provider, installation.vault.provider) || "infisical",
          region: normalizeString(body.vault_region, installation.vault.region) || "EU",
        },
        selected_agents: selectedAgents,
        bootstrap: {
          last_written_at: installation.bootstrap.last_written_at,
          last_repo_path: installation.bootstrap.last_repo_path,
          files_written: installation.bootstrap.files_written,
        },
        completed_at: completedAt,
        updated_at: updatedAt,
      },
      templates: {
        demo: buildDemoTemplate(team, projects),
        growth: buildGrowthTemplate(kanbanUrl, crmUrl),
      },
    },
    team,
    projects,
  };
}

function replaceTokens(content, replacements) {
  let output = content;
  for (const [key, value] of Object.entries(replacements)) {
    const token = new RegExp(`{{${key}}}`, "g");
    output = output.replace(token, value);
  }
  return output;
}

function ensureTextFile(targetPath, content) {
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
  fs.writeFileSync(targetPath, content, "utf8");
}

function appendGitignore(repoPath) {
  const targetPath = path.join(repoPath, ".gitignore");
  const block = [
    "",
    "# AgentFleet managed secrets",
    ".env",
    ".env.*",
  ].join("\n");
  let current = "";
  if (fileExists(targetPath)) current = fs.readFileSync(targetPath, "utf8");
  if (current.includes("# AgentFleet managed secrets")) return;
  ensureTextFile(targetPath, `${current.replace(/\s*$/, "")}${block}\n`);
}

function walkDirectory(rootPath) {
  const entries = [];
  for (const dirent of fs.readdirSync(rootPath, { withFileTypes: true })) {
    const fullPath = path.join(rootPath, dirent.name);
    if (dirent.isDirectory()) {
      entries.push(...walkDirectory(fullPath));
    } else {
      entries.push(fullPath);
    }
  }
  return entries;
}

function copyBlueprintTree(sourceRoot, targetRoot, replacements, filesWritten) {
  const files = walkDirectory(sourceRoot);
  for (const sourcePath of files) {
    const relativePath = path.relative(sourceRoot, sourcePath);
    const targetPath = path.join(targetRoot, relativePath);
    const ext = path.extname(sourcePath).toLowerCase();
    fs.mkdirSync(path.dirname(targetPath), { recursive: true });
    if (TEXT_FILE_EXTENSIONS.has(ext)) {
      const raw = fs.readFileSync(sourcePath, "utf8");
      ensureTextFile(targetPath, replaceTokens(raw, replacements));
    } else {
      fs.copyFileSync(sourcePath, targetPath);
    }
    filesWritten.push(relativePath.replace(/\\/g, "/"));
  }
}

function buildRootAgentDocs(orgName, selectedAgents) {
  const agentIds = new Set(selectedAgents.map(agent => agent.id));
  const files = {
    "AGENTS.md": [
      `# ${orgName} Agent Instructions`,
      "",
      "Read `MISSION_CONTROL.md` before doing anything else.",
      "Read `AGENTS/RULES.md` before making changes.",
      "Check `AGENTS/MESSAGES/inbox.json` at session start.",
      "",
      "Update standups before closing a session.",
    ].join("\n"),
  };

  if (agentIds.has("claude_code")) {
    files["CLAUDE.md"] = [
      `# ${orgName} Claude Code Bootstrap`,
      "",
      "Read `MISSION_CONTROL.md` first.",
      "Then read `AGENTS/RULES.md`.",
      "Use `AGENTS/MESSAGES/inbox.json` for handoffs and updates.",
    ].join("\n");
  }

  if (agentIds.has("gemini_cli")) {
    files["GEMINI.md"] = [
      `# ${orgName} Gemini CLI Bootstrap`,
      "",
      "Read `MISSION_CONTROL.md` first.",
      "Then read `AGENTS/RULES.md`.",
      "Use `AGENTS/MESSAGES/inbox.json` for handoffs and updates.",
    ].join("\n");
  }

  return files;
}

function buildMissionControlReplacements(meta) {
  const installation = meta.meta.installation;
  const selectedAgents = installation.selected_agents;
  const projectPath = installation.repo_path ? "." : "{{PROJECT_PATH}}";
  const projectDesc = `${installation.org_name} multi-agent workspace`;
  const roster = [...selectedAgents, null];

  return {
    PROJECT_NAME: installation.org_name,
    ORG_NAME: installation.org_name,
    PROJECT_PATH: projectPath,
    PROJECT_REPO_URL: installation.repo_url || "#",
    PROJECT_DESC: projectDesc,
    KANBAN_URL: installation.kanban_url || "#",
    CRM_URL: installation.crm_url || "#",
    AGENT_1_NAME: roster[0]?.name || "Coordinator",
    AGENT_1_MODEL: roster[0]?.label || "claude-sonnet-4-6",
    AGENT_1_ROLE: roster[0] ? AGENT_PRESETS[roster[0].id].roleTitle : "Coordinator",
    AGENT_2_NAME: roster[1]?.name || "Builder",
    AGENT_2_MODEL: roster[1]?.label || "codex",
    AGENT_2_ROLE: roster[1] ? AGENT_PRESETS[roster[1].id].roleTitle : "Implementation",
    FIRST_TICKET_DESCRIPTION: "Run setup, validate generated files, and start the first delivery ticket.",
    SECRET_1_NAME: "KANBAN_TOKEN",
    SECRET_1_DESC: "GitHub or project board token for automation.",
    SECRET_1_APP: "Kanban bridge",
  };
}

export function writeBootstrapFiles(meta, repoPathInput) {
  const rawRepoPath = normalizeString(repoPathInput || meta.meta.installation.repo_path);
  if (!rawRepoPath) {
    throw new Error("repo_path_required");
  }
  const repoPath = path.resolve(rawRepoPath);

  fs.mkdirSync(repoPath, { recursive: true });
  const filesWritten = [];
  const replacements = buildMissionControlReplacements(meta);

  copyBlueprintTree(BLUEPRINT_ROOT, repoPath, replacements, filesWritten);

  writeJson(path.join(repoPath, "AGENTS", "CONFIG", "fleet_meta.json"), meta);
  filesWritten.push("AGENTS/CONFIG/fleet_meta.json");
  writeJson(path.join(repoPath, "AGENTS", "CONFIG", "demo_meta.json"), meta.meta.templates.demo || buildDemoTemplate(meta.team, meta.projects));
  filesWritten.push("AGENTS/CONFIG/demo_meta.json");
  writeJson(path.join(repoPath, "AGENTS", "CONFIG", "growth_meta.json"), meta.meta.templates.growth || buildGrowthTemplate(meta.meta.installation.kanban_url, meta.meta.installation.crm_url));
  filesWritten.push("AGENTS/CONFIG/growth_meta.json");
  writeJson(path.join(repoPath, "standups", "index.json"), []);
  filesWritten.push("standups/index.json");

  const rootDocs = buildRootAgentDocs(meta.meta.installation.org_name, meta.meta.installation.selected_agents);
  for (const [relativePath, content] of Object.entries(rootDocs)) {
    ensureTextFile(path.join(repoPath, relativePath), content);
    filesWritten.push(relativePath);
  }

  appendGitignore(repoPath);
  filesWritten.push(".gitignore");

  return {
    repo_path: repoPath,
    files_written: Array.from(new Set(filesWritten)).sort(),
  };
}

export function getBootstrapInstructions(meta) {
  const selected = meta.meta.installation.selected_agents || [];
  return selected.map(agent => ({
    id: agent.id,
    label: agent.label,
    name: agent.name,
    instruction: AGENT_PRESETS[agent.id]?.bootstrapInstruction || "",
  }));
}

export function runDoctor(meta) {
  const normalized = normalizeFleetMeta(meta);
  const installation = normalized.meta.installation;
  const issues = [];
  const checks = [];

  function addCheck(id, ok, detail) {
    checks.push({ id, ok, detail });
    if (!ok) issues.push(detail);
  }

  addCheck("org_name", Boolean(installation.org_name), "Organization name is missing.");
  addCheck("selected_agents", installation.selected_agents.length > 0, "At least one agent must be selected.");
  addCheck("vault_provider", Boolean(installation.vault.provider), "Vault provider is missing.");

  if (installation.repo_path) {
    const repoPath = path.resolve(installation.repo_path);
    addCheck("repo_path_exists", fileExists(repoPath), `Repository path does not exist: ${repoPath}`);
    addCheck("repo_git", fileExists(path.join(repoPath, ".git")), `Repository path is not a git repository: ${repoPath}`);

    const requiredFiles = [
      "MISSION_CONTROL.md",
      "AGENTS.md",
      "AGENTS/RULES.md",
      "AGENTS/KEYVAULT.md",
      "AGENTS/CONFIG/fleet_meta.json",
      "AGENTS/CONFIG/growth_meta.json",
      "AGENTS/MESSAGES/inbox.json",
      "AGENTS/LESSONS/ledger.json",
      "standups/index.json",
      "vault/README.md",
      "vault/vault.py",
      "vault/agent-fetch.sh",
      "vault/agent-fetch.ps1",
    ];

    for (const relativePath of requiredFiles) {
      addCheck(
        `file:${relativePath}`,
        fileExists(path.join(repoPath, relativePath)),
        `Missing bootstrap file: ${relativePath}`
      );
    }

    if (installation.selected_agents.some(agent => agent.id === "claude_code")) {
      addCheck("file:CLAUDE.md", fileExists(path.join(repoPath, "CLAUDE.md")), "Missing agent bootstrap file: CLAUDE.md");
    }
    if (installation.selected_agents.some(agent => agent.id === "gemini_cli")) {
      addCheck("file:GEMINI.md", fileExists(path.join(repoPath, "GEMINI.md")), "Missing agent bootstrap file: GEMINI.md");
    }
  }

  return {
    ok: issues.length === 0,
    checks,
    issues,
  };
}

export function getSetupStatus(meta) {
  const normalized = normalizeFleetMeta(meta);
  return {
    completed: normalized.meta.installation.setup_completed,
    profile: normalized.meta.installation,
    bootstrap_instructions: getBootstrapInstructions(normalized),
    doctor: runDoctor(normalized),
    catalog: getAgentCatalog(),
  };
}

export function updateBootstrapMetadata(meta, bootstrapResult) {
  const normalized = normalizeFleetMeta(meta);
  normalized.meta.installation.bootstrap = {
    last_written_at: isoNow(),
    last_repo_path: bootstrapResult.repo_path,
    files_written: bootstrapResult.files_written,
  };
  normalized.meta.installation.updated_at = isoNow();
  return normalized;
}

export function getDemoConfig(meta, fallback) {
  const normalized = normalizeFleetMeta(meta);
  const template = normalized.meta?.templates?.demo;
  if (template?.team?.length || template?.projects?.length) return template;
  return fallback;
}

export function getGrowthConfig(meta, fallback) {
  const normalized = normalizeFleetMeta(meta);
  const template = normalized.meta?.templates?.growth;
  if (template?.team?.length || template?.projects?.length) return template;
  return fallback;
}

export function buildSlug(value) {
  return slugify(value);
}
