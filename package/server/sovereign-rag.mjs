import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFile, execFileSync } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const EMBEDDING_DIMENSIONS = 384;
const MIN_CHUNK_TOKENS = 256;
const TARGET_CHUNK_TOKENS = 384;
const MAX_CHUNK_TOKENS = 512;
const CHUNK_OVERLAP_TOKENS = 48;
const MAX_COLLECTION_CHUNKS = 5_000;
const INDEX_KIND = "faiss_flat";

const EXAMPLE_PERSONAS = [
  {
    id: "field-engineer",
    name: "Field Engineer",
    summary: "Prioritizes diagnostics, safety steps, observed symptoms, and next actions.",
    system_prompt:
      "You are Sovereign Mind in Field Engineer mode. Answer from the provided RAG context first. Be concrete, operational, and safety-aware. Start with the most likely diagnosis, list checks in the order a technician should perform them, call out lockout/tagout or escalation needs, and cite source chunk IDs when available. If the context is insufficient, say exactly what measurement, log, photo, or manual section is missing.",
  },
  {
    id: "product-manager",
    name: "Product Manager",
    summary: "Turns source material into customer impact, requirements, tradeoffs, and rollout notes.",
    system_prompt:
      "You are Sovereign Mind in Product Manager mode. Answer from the provided RAG context first. Translate technical details into user impact, requirements, risks, dependencies, and release decisions. Keep recommendations scoped and cite source chunk IDs when available. If evidence is missing, state the assumption and identify what stakeholder or document should confirm it.",
  },
  {
    id: "technical-writer",
    name: "Technical Writer",
    summary: "Produces clear documentation, SOP text, release notes, and source-grounded explanations.",
    system_prompt:
      "You are Sovereign Mind in Technical Writer mode. Answer from the provided RAG context first. Write concise, structured documentation that a new operator can follow. Prefer headings, numbered procedures, warnings, and glossary definitions. Preserve source terminology, avoid unsupported claims, and cite source chunk IDs when available. If the material conflicts, identify the conflict before drafting final text.",
  },
];

function repeatParagraphs(paragraphs, cycles = 18) {
  const rows = [];
  for (let i = 0; i < cycles; i += 1) {
    for (const paragraph of paragraphs) rows.push(paragraph);
  }
  return rows.join("\n\n");
}

const EXAMPLE_INDEX_SPECS = [
  {
    id: "robot-ross-atf",
    version_id: "example-robot-ross-atf-v1",
    title: "Robot Ross ATF Wiki",
    domain: "Automated technical file",
    description: "Robot Ross operational wiki with compliance, job orchestration, hardware interface, calibration, narration, and video proof references.",
    sources: [
      {
        id: "atf-overview",
        name: "Robot Ross ATF Overview.md",
        text: repeatParagraphs([
          "Robot Ross is a robot painting system with an automated technical file. The ATF records the architecture, order flow, operational ledger, wiki pages, and cited question answering layer so an operator can explain what the robot did and why.",
          "The system treats every job as traceable evidence. Shopify order data, bidding decisions, calibration events, hardware commands, narration, and video proof are compiled into reference pages that can be queried locally.",
          "A compliant answer should cite the relevant ATF page, distinguish observed events from generated summaries, and preserve the chain from customer request to robot action."
        ]),
      },
      {
        id: "atf-hardware",
        name: "Robot Ross Hardware Interface.md",
        text: repeatParagraphs([
          "The hardware interface controls robot motion, brush handling, drawing surfaces, and job state transitions. Operators verify the arm is homed, the work area is clear, and the drawing surface is registered before a painting job starts.",
          "Calibration aligns the physical canvas with the coordinate system used by generated drawing paths. A failed calibration blocks production because later path commands may be accurate in software but unsafe or misplaced in the physical cell.",
          "When troubleshooting a job, inspect the command ledger, robot status, calibration timestamp, and video proof before changing hardware parameters."
        ]),
      },
      {
        id: "atf-compliance",
        name: "Robot Ross Compliance.md",
        text: repeatParagraphs([
          "The ATF supports transparency and oversight by keeping a local evidence trail. The wiki summarizes sources, while raw ledgers remain the authority for exact event timing and machine actions.",
          "EU AI Act alignment depends on logging, transparency, human oversight, and traceability. The ATF does not replace engineering judgment; it gives reviewers a grounded record for audits and incident review.",
          "If a generated explanation cannot be traced to a ledger event or wiki source, the answer must say the evidence is unavailable instead of inventing a justification."
        ]),
      },
    ],
  },
  {
    id: "industrial-troubleshooting",
    version_id: "example-industrial-troubleshooting-v1",
    title: "Industrial Troubleshooting Guide",
    domain: "Generic industrial operations",
    description: "Domain-agnostic maintenance guide for pumps, conveyors, sensors, PLC alarms, lockout/tagout, and shift handover.",
    sources: [
      {
        id: "industrial-safety",
        name: "Industrial Safety and Isolation.md",
        text: repeatParagraphs([
          "Before inspecting moving equipment, isolate energy sources, apply lockout/tagout, verify zero energy, and communicate the work boundary to the shift lead. Never bypass an interlock to speed diagnosis.",
          "Escalate immediately when a fault involves exposed conductors, unknown stored pressure, repeated emergency stops, smoke, abnormal heat, or safety device tampering.",
          "A good troubleshooting note records symptom, asset ID, alarm code, first observed time, operating mode, recent changes, checks performed, and the decision to return to service or escalate."
        ]),
      },
      {
        id: "industrial-pumps",
        name: "Pump and Hydraulic Troubleshooting.md",
        text: repeatParagraphs([
          "Low pump output can come from blocked inlet strainers, air ingress, worn impellers, incorrect rotation, closed valves, low reservoir level, or a pressure relief valve stuck open.",
          "Hydraulic pressure drift should be checked with a calibrated gauge at the test port, then compared against the HMI value. If the gauge and HMI disagree, inspect the pressure transducer, wiring, scaling, and PLC input card.",
          "Cavitation symptoms include rattling noise, vibration, fluctuating discharge pressure, and loss of flow. Stop and inspect suction conditions before increasing speed or forcing production."
        ]),
      },
      {
        id: "industrial-controls",
        name: "PLC Sensors and Conveyor Faults.md",
        text: repeatParagraphs([
          "For a conveyor no-start condition, check emergency stop chain, guard doors, drive ready state, overload reset, permissive sensors, jam detection, and whether the PLC is holding a fault latch.",
          "Photo-eye failures are often caused by dirty lenses, misalignment, reflective targets, damaged cables, incorrect teach settings, or lighting changes. Clean and align before replacing the sensor.",
          "When a PLC alarm repeats after reset, compare the alarm timestamp with mechanical observations and recent maintenance. Repeated alarms should not be cleared without identifying the triggering condition."
        ]),
      },
    ],
  },
];

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJson(filePath, fallback) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return fallback;
  }
}

function writeJson(filePath, value) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function stableId(prefix, input) {
  return `${prefix}-${crypto.createHash("sha256").update(input).digest("hex").slice(0, 16)}`;
}

function normalizeDocumentName(name) {
  const base = String(name || "document.txt").replace(/[^\w .()-]/g, "_").trim();
  return base || "document.txt";
}

function extensionForDocument(doc) {
  const nameExt = path.extname(String(doc.name || "")).toLowerCase();
  if ([".pdf", ".docx", ".txt", ".md", ".csv"].includes(nameExt)) return nameExt;
  const type = String(doc.type || "").toLowerCase();
  if (type.includes("pdf")) return ".pdf";
  if (type.includes("wordprocessingml") || type.includes("docx")) return ".docx";
  if (type.includes("markdown")) return ".md";
  if (type.includes("csv")) return ".csv";
  return ".txt";
}

function documentPhase(name, progress, error = null) {
  return {
    name,
    status: error ? "failed" : name,
    progress,
    at: new Date().toISOString(),
    error,
  };
}

function getPaths(baseDir) {
  const root = path.join(baseDir, "sovereign");
  return {
    root,
    state: path.join(root, "console.json"),
    documents: path.join(root, "documents"),
    packages: path.join(root, "packages"),
    logs: path.join(root, "logs"),
  };
}

function defaultState() {
  return {
    account: {
      id: "corp-default",
      name: "Corporate Knowledge",
      domain: "example.com",
      plan: "Corporate",
      oauthProviders: ["Google", "Azure"],
      lastIndexedAt: null,
      version: "Draft",
      docListFingerprint: null,
      packageUrl: null,
      lastError: null,
    },
    users: [],
    documents: [],
    packages: [],
    examples: [],
    personas: EXAMPLE_PERSONAS,
    notifications: [],
  };
}

export function loadSovereignState(baseDir) {
  const paths = getPaths(baseDir);
  const state = readJson(paths.state, defaultState());
  const fallback = defaultState();
  return {
    ...fallback,
    ...state,
    account: { ...fallback.account, ...(state.account || {}) },
    users: Array.isArray(state.users) ? state.users : [],
    documents: Array.isArray(state.documents) ? state.documents : [],
    packages: Array.isArray(state.packages) ? state.packages : [],
    examples: Array.isArray(state.examples) ? state.examples : [],
    personas: Array.isArray(state.personas) && state.personas.length ? state.personas : EXAMPLE_PERSONAS,
    notifications: Array.isArray(state.notifications) ? state.notifications : [],
  };
}

export function saveSovereignState(baseDir, state) {
  writeJson(getPaths(baseDir).state, state);
  return state;
}

export function inviteSovereignUser(baseDir, email) {
  const clean = String(email || "").trim().toLowerCase();
  if (!clean || !clean.includes("@")) throw new Error("valid_email_required");
  const state = loadSovereignState(baseDir);
  const existing = state.users.find((user) => user.email === clean);
  if (existing) {
    existing.status = "active";
  } else {
    state.users.push({ email: clean, role: "Member", status: "active", invitedAt: new Date().toISOString() });
  }
  return saveSovereignState(baseDir, state);
}

export function setSovereignUserDisabled(baseDir, email, disabled) {
  const clean = String(email || "").trim().toLowerCase();
  const state = loadSovereignState(baseDir);
  const user = state.users.find((item) => item.email === clean);
  if (!user) throw new Error("user_not_found");
  user.status = disabled ? "disabled" : "active";
  return saveSovereignState(baseDir, state);
}

export function addSovereignDocuments(baseDir, documents) {
  const paths = getPaths(baseDir);
  ensureDir(paths.documents);
  const state = loadSovereignState(baseDir);
  const incoming = Array.isArray(documents) ? documents : [];
  for (const doc of incoming) {
    const name = normalizeDocumentName(doc.name);
    const contentBase64 = typeof doc.contentBase64 === "string" ? doc.contentBase64 : "";
    const pdfBytes = contentBase64 ? Buffer.from(contentBase64, "base64") : null;
    const id = doc.id || stableId("doc", `${name}:${doc.size || 0}:${contentBase64.slice(0, 64)}:${Date.now()}`);
    const ext = extensionForDocument({ ...doc, name });
    const fileName = `${id}${ext}`;
    const originalPath = path.join(paths.documents, fileName);
    if (pdfBytes?.length) fs.writeFileSync(originalPath, pdfBytes);
    const record = {
      id,
      name,
      size: Number(doc.size || pdfBytes?.length || 0),
      type: doc.type || "text/plain",
      status: "pending",
      progress: 0,
      failure_state: null,
      indexed: false,
      references: 0,
      exclude: false,
      notes: "",
      processing_steps: [documentPhase("pending", 0)],
      uploadedAt: new Date().toISOString(),
      originalPath: pdfBytes?.length ? originalPath : null,
      sha256: pdfBytes?.length ? crypto.createHash("sha256").update(pdfBytes).digest("hex") : null,
      error: null,
    };
    const existingIndex = state.documents.findIndex((item) => item.id === id);
    if (existingIndex === -1) {
      state.documents.push(record);
    } else {
      state.documents[existingIndex] = { ...state.documents[existingIndex], ...record };
    }
  }
  return saveSovereignState(baseDir, state);
}

export function patchSovereignDocument(baseDir, id, patch) {
  const state = loadSovereignState(baseDir);
  const doc = state.documents.find((item) => item.id === id);
  if (!doc) throw new Error("document_not_found");
  if (typeof patch.exclude === "boolean") doc.exclude = patch.exclude;
  if (typeof patch.notes === "string") doc.notes = patch.notes.slice(0, 4000);
  return saveSovereignState(baseDir, state);
}

function tokenize(text) {
  return String(text || "").match(/\S+/g) || [];
}

function detokenize(tokens) {
  return tokens.join(" ").replace(/\s+([,.;:!?])/g, "$1");
}

function splitSemanticUnits(text) {
  const normalized = String(text || "").replace(/\r/g, "\n").replace(/[ \t]+/g, " ").trim();
  const paragraphs = normalized.split(/\n{2,}/).map((p) => p.trim()).filter(Boolean);
  const units = [];
  for (const paragraph of paragraphs.length ? paragraphs : [normalized]) {
    const sentences = paragraph.match(/[^.!?\n]+[.!?]?(?:\s+|$)/g) || [paragraph];
    for (const sentence of sentences) {
      const clean = sentence.trim();
      if (clean) units.push(clean);
    }
  }
  return units;
}

export function chunkText(text, source) {
  const chunks = [];
  const units = splitSemanticUnits(text);
  let current = [];
  let currentTokens = 0;
  let chunkIndex = 0;

  function emit() {
    if (!current.length) return;
    const bodyTokens = current.flatMap(tokenize);
    if (!bodyTokens.length) return;
    chunks.push({
      id: `${source.id}#chunk-${String(chunkIndex + 1).padStart(4, "0")}`,
      chunk_index: chunkIndex,
      source_doc_id: source.id,
      source_doc_name: source.name,
      text: detokenize(bodyTokens),
      token_count: bodyTokens.length,
    });
    chunkIndex += 1;
    const overlap = bodyTokens.slice(-CHUNK_OVERLAP_TOKENS);
    current = overlap.length ? [detokenize(overlap)] : [];
    currentTokens = overlap.length;
  }

  for (const unit of units) {
    const unitTokens = tokenize(unit);
    if (unitTokens.length > MAX_CHUNK_TOKENS) {
      if (currentTokens >= MIN_CHUNK_TOKENS) emit();
      for (let i = 0; i < unitTokens.length; i += TARGET_CHUNK_TOKENS - CHUNK_OVERLAP_TOKENS) {
        const windowTokens = unitTokens.slice(i, i + TARGET_CHUNK_TOKENS);
        if (windowTokens.length) {
          current = [detokenize(windowTokens)];
          currentTokens = windowTokens.length;
          emit();
        }
      }
      continue;
    }
    if (currentTokens + unitTokens.length > MAX_CHUNK_TOKENS) emit();
    current.push(unit);
    currentTokens += unitTokens.length;
    if (currentTokens >= TARGET_CHUNK_TOKENS) emit();
  }
  if (currentTokens) {
    if (chunks.length && currentTokens < MIN_CHUNK_TOKENS) {
      const previous = chunks[chunks.length - 1];
      const merged = tokenize(`${previous.text} ${detokenize(current.flatMap(tokenize))}`).slice(0, MAX_CHUNK_TOKENS);
      previous.text = detokenize(merged);
      previous.token_count = merged.length;
    } else {
      emit();
    }
  }
  return chunks;
}

function decodePdfLiteral(raw) {
  return raw
    .replace(/\\([nrtbf()\\])/g, (_m, ch) => ({ n: "\n", r: "\r", t: "\t", b: "\b", f: "\f", "(": "(", ")": ")", "\\": "\\" })[ch] || ch)
    .replace(/\\([0-7]{1,3})/g, (_m, octal) => String.fromCharCode(parseInt(octal, 8)));
}

function fallbackPdfText(buffer) {
  const latin = buffer.toString("latin1");
  const literals = [];
  const textOps = latin.matchAll(/\((?:\\.|[^\\)])*\)\s*T[Jj]/g);
  for (const op of textOps) {
    const literalMatches = op[0].matchAll(/\(((?:\\.|[^\\)])*)\)/g);
    for (const literal of literalMatches) literals.push(decodePdfLiteral(literal[1]));
  }
  if (literals.join(" ").trim().length > 40) return literals.join("\n");
  return latin
    .replace(/[^\x09\x0a\x0d\x20-\x7e]+/g, " ")
    .split(/\s{2,}/)
    .filter((part) => /[A-Za-z]{3,}/.test(part))
    .join("\n");
}

export async function extractPdfText(filePath) {
  const buffer = fs.readFileSync(filePath);
  try {
    const { stdout } = await execFileAsync("pdftotext", ["-layout", "-enc", "UTF-8", filePath, "-"], {
      maxBuffer: 100 * 1024 * 1024,
      timeout: 60_000,
    });
    if (stdout.trim()) return stdout;
  } catch {
    // Deployment can install poppler for better extraction; fallback keeps the pipeline local.
  }
  return fallbackPdfText(buffer);
}

function decodeXmlText(xml) {
  return String(xml || "")
    .replace(/<w:tab\/>/g, "\t")
    .replace(/<w:br\/>/g, "\n")
    .replace(/<\/w:p>/g, "\n\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, "\"")
    .replace(/&apos;/g, "'")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export async function extractDocxText(filePath) {
  try {
    const { stdout } = await execFileAsync("unzip", ["-p", filePath, "word/document.xml"], {
      maxBuffer: 100 * 1024 * 1024,
      timeout: 60_000,
    });
    return decodeXmlText(stdout);
  } catch (error) {
    throw new Error(`docx_text_extraction_failed:${path.basename(filePath)}:${error.message}`);
  }
}

export async function extractDocumentText(doc) {
  if (!doc.originalPath || !fs.existsSync(doc.originalPath)) {
    throw new Error(`missing_document:${doc.name}`);
  }
  const ext = path.extname(doc.originalPath).toLowerCase();
  const type = String(doc.type || "").toLowerCase();
  if (ext === ".pdf" || type.includes("pdf")) return extractPdfText(doc.originalPath);
  if (ext === ".docx" || type.includes("wordprocessingml") || type.includes("docx")) return extractDocxText(doc.originalPath);
  if ([".txt", ".md", ".csv"].includes(ext) || type.startsWith("text/")) {
    return fs.readFileSync(doc.originalPath, "utf8");
  }
  throw new Error(`unsupported_document_type:${doc.name}`);
}

export function embedText(text) {
  const vector = new Array(EMBEDDING_DIMENSIONS).fill(0);
  const tokens = tokenize(String(text || "").toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, " "));
  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i];
    const hash = crypto.createHash("sha256").update(token).digest();
    const idx = hash.readUInt16BE(0) % EMBEDDING_DIMENSIONS;
    const sign = (hash[2] & 1) === 0 ? 1 : -1;
    vector[idx] += sign;
    if (i < tokens.length - 1) {
      const bigramHash = crypto.createHash("sha256").update(`${token} ${tokens[i + 1]}`).digest();
      vector[bigramHash.readUInt16BE(0) % EMBEDDING_DIMENSIONS] += (bigramHash[2] & 1) === 0 ? 0.5 : -0.5;
    }
  }
  const norm = Math.sqrt(vector.reduce((sum, value) => sum + value * value, 0)) || 1;
  return vector.map((value) => Number((value / norm).toFixed(6)));
}

function cosine(a, b) {
  let sum = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i += 1) sum += a[i] * b[i];
  return sum;
}

function writeJsonl(filePath, rows) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, rows.map((row) => JSON.stringify(row)).join("\n") + "\n");
}

function docFingerprint(documents) {
  const source = documents
    .map((doc) => `${doc.id}:${doc.sha256 || ""}:${doc.name}:${doc.exclude ? "excluded" : "included"}`)
    .sort()
    .join("\n");
  return crypto.createHash("sha256").update(source).digest("hex");
}

function buildWiki(metadata, documents, chunks) {
  const byDoc = new Map();
  for (const chunk of chunks) {
    if (!byDoc.has(chunk.source_doc_id)) byDoc.set(chunk.source_doc_id, []);
    byDoc.get(chunk.source_doc_id).push(chunk);
  }
  const lines = [
    `# ${metadata.collection_title || "Sovereign Mind Collection"}`,
    "",
    `Generated: ${metadata.generated_at}`,
    `Version: ${metadata.version_id}`,
    `Document fingerprint: ${metadata.doc_list_fingerprint}`,
    `Index: ${metadata.index.kind} (${metadata.index.metric}, ${metadata.embedding_dimensions} dimensions)`,
    `Chunks: ${metadata.chunk_count}`,
    "",
    "## Collection Summary",
    "",
    `This version contains ${metadata.document_status.succeeded} ingested document(s), ${metadata.document_status.failed} failed document(s), and ${metadata.chunk_count} searchable chunks. Retrieval uses the top 5 matching chunks by default.`,
    "",
    "## Source Documents",
    "",
  ];
  for (const doc of documents) {
    const docChunks = byDoc.get(doc.id) || [];
    lines.push(`### ${doc.name}`, "");
    lines.push(`- Document ID: \`${doc.id}\``);
    lines.push(`- Status: ${doc.status}`);
    lines.push(`- SHA-256: \`${doc.sha256 || "unavailable"}\``);
    lines.push(`- Chunks: ${docChunks.length}`);
    if (doc.error) lines.push(`- Failure: ${doc.error}`);
    if (doc.notes) lines.push(`- Admin notes: ${doc.notes}`);
    lines.push("");
    if (!docChunks.length) continue;
    for (const chunk of docChunks) {
      lines.push(`#### ${chunk.id}`);
      lines.push("");
      lines.push(`Tokens: ${chunk.token_count}`);
      lines.push(`Source: ${chunk.source_doc_name}`);
      lines.push("");
      lines.push(chunk.text.slice(0, 700));
      lines.push("");
    }
  }
  return `${lines.join("\n")}\n`;
}

async function zipDirectory(sourceDir, zipPath) {
  try {
    await execFileAsync("zip", ["-qr", zipPath, "."], { cwd: sourceDir, timeout: 120_000 });
  } catch (error) {
    throw new Error(`zip_failed:${error.message}`);
  }
}

function zipDirectorySync(sourceDir, zipPath) {
  try {
    execFileSync("zip", ["-qr", zipPath, "."], { cwd: sourceDir, timeout: 120_000 });
  } catch (error) {
    throw new Error(`zip_failed:${error.message}`);
  }
}

function sourceRecord(source) {
  return {
    id: source.id,
    name: source.name,
    sha256: crypto.createHash("sha256").update(source.text).digest("hex"),
    notes: "",
  };
}

function buildExamplePackage(baseDir, spec) {
  const paths = getPaths(baseDir);
  const versionId = spec.version_id;
  const packageDir = path.join(paths.packages, versionId);
  const bundleDir = path.join(packageDir, "bundle");
  const zipPath = path.join(packageDir, `${versionId}.zip`);
  const downloadUrl = `/fleet/api/sovereign/rag/packages/${encodeURIComponent(versionId)}/download`;

  if (!fs.existsSync(zipPath)) {
    fs.rmSync(packageDir, { recursive: true, force: true });
    ensureDir(bundleDir);
    const generatedAt = "2026-07-16T00:00:00.000Z";
    const documents = spec.sources.map(sourceRecord);
    const fingerprint = crypto
      .createHash("sha256")
      .update(spec.sources.map((source) => `${source.id}:${source.name}:${source.text}`).join("\n"))
      .digest("hex");
    const chunks = [];
    for (const source of spec.sources) {
      chunks.push(...chunkText(source.text, sourceRecord(source)));
    }
    const embeddings = chunks.map((chunk) => ({
      chunk_id: chunk.id,
      vector: embedText(chunk.text),
    }));
    const metadata = {
      version_id: versionId,
      generated_at: generatedAt,
      customer_id: "trial",
      example_id: spec.id,
      example_title: spec.title,
      doc_list_fingerprint: fingerprint,
      embedding_model: "local-hashing-embedding-v1",
      embedding_dimensions: EMBEDDING_DIMENSIONS,
      index: {
        kind: INDEX_KIND,
        metric: "cosine",
        faiss_factory: "Flat",
      },
      personas: EXAMPLE_PERSONAS.map((persona) => ({
        id: persona.id,
        name: persona.name,
        summary: persona.summary,
        system_prompt: persona.system_prompt,
      })),
      chunking: {
        min_tokens: MIN_CHUNK_TOKENS,
        target_tokens: TARGET_CHUNK_TOKENS,
        max_tokens: MAX_CHUNK_TOKENS,
        overlap_tokens: CHUNK_OVERLAP_TOKENS,
        max_collection_chunks: MAX_COLLECTION_CHUNKS,
      },
      documents: documents.map((doc) => ({
        id: doc.id,
        name: doc.name,
        sha256: doc.sha256,
        status: "published",
        chunks: chunks.filter((chunk) => chunk.source_doc_id === doc.id).length,
      })),
      document_status: {
        total: documents.length,
        succeeded: documents.length,
        failed: 0,
      },
      chunk_count: chunks.length,
    };

    writeJsonl(path.join(bundleDir, "chunks.jsonl"), chunks);
    writeJsonl(path.join(bundleDir, "embeddings.jsonl"), embeddings);
    writeJson(path.join(bundleDir, "metadata.json"), metadata);
    fs.writeFileSync(path.join(bundleDir, "wiki.md"), buildWiki(metadata, documents, chunks));
    zipDirectorySync(bundleDir, zipPath);
  }

  const sizeBytes = fs.statSync(zipPath).size;
  return {
    id: spec.id,
    version_id: versionId,
    title: spec.title,
    domain: spec.domain,
    description: spec.description,
    free: true,
    auth_required: false,
    chunk_count: readJson(path.join(bundleDir, "metadata.json"), {}).chunk_count || 0,
    size_bytes: sizeBytes,
    download_url: downloadUrl,
    local_path: zipPath,
  };
}

export function ensureSovereignExamples(baseDir) {
  return EXAMPLE_INDEX_SPECS.map((spec) => buildExamplePackage(baseDir, spec));
}

export function getSovereignPersonas() {
  return EXAMPLE_PERSONAS.map((persona) => ({ ...persona }));
}

export function loadSovereignConsoleState(baseDir) {
  const state = loadSovereignState(baseDir);
  return {
    ...state,
    examples: ensureSovereignExamples(baseDir),
    personas: getSovereignPersonas(),
  };
}

function appendFailure(paths, message) {
  ensureDir(paths.logs);
  fs.appendFileSync(path.join(paths.logs, "rag-generation.log"), `${new Date().toISOString()} ${message}\n`);
}

function markDocument(doc, status, progress, error = null) {
  doc.status = status;
  doc.progress = progress;
  doc.error = error;
  doc.failure_state = error ? status : null;
  if (!Array.isArray(doc.processing_steps)) doc.processing_steps = [];
  doc.processing_steps.push(documentPhase(status, progress, error));
}

export async function generateRagIndex(baseDir, options = {}) {
  const paths = getPaths(baseDir);
  let state = loadSovereignState(baseDir);
  const customerId = options.account_id || state.account.id || "corp-default";
  const selectedDocs = state.documents.filter((doc) => !doc.exclude);
  if (!selectedDocs.length) throw new Error("no_documents_selected");

  for (const doc of selectedDocs) {
    markDocument(doc, "queued", 5);
    doc.indexed = false;
    doc.references = 0;
  }
  saveSovereignState(baseDir, state);

  try {
    const generatedAt = new Date().toISOString();
    const fingerprint = docFingerprint(selectedDocs);
    const versionId = `rag-${generatedAt.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z")}-${fingerprint.slice(0, 12)}`;
    const packageDir = path.join(paths.packages, versionId);
    const bundleDir = path.join(packageDir, "bundle");
    ensureDir(bundleDir);

    const allChunks = [];
    const publishedDocs = [];
    const failedDocs = [];
    for (const doc of selectedDocs) {
      try {
        markDocument(doc, "extracting_text", 20);
        saveSovereignState(baseDir, state);
        const text = await extractDocumentText(doc);
        if (tokenize(text).length < 20) throw new Error(`needs_ocr:${doc.name}`);

        markDocument(doc, "chunking", 45);
        saveSovereignState(baseDir, state);
        const chunks = chunkText(text, doc);
        if (!chunks.length) throw new Error(`no_chunks_generated:${doc.name}`);
        if (allChunks.length + chunks.length > MAX_COLLECTION_CHUNKS) {
          throw new Error(`max_chunks_exceeded:${doc.name}:${allChunks.length + chunks.length}/${MAX_COLLECTION_CHUNKS}`);
        }

        markDocument(doc, "embedding", 70);
        saveSovereignState(baseDir, state);
        for (const chunk of chunks) allChunks.push(chunk);
        doc.references = chunks.length;
        doc.indexed = true;
        markDocument(doc, "published", 100);
        saveSovereignState(baseDir, state);
        publishedDocs.push(doc);
      } catch (error) {
        const message = error.message || String(error);
        const status = message.startsWith("needs_ocr:") ? "needs_ocr" : "failed";
        doc.references = 0;
        doc.indexed = false;
        markDocument(doc, status, 100, message);
        saveSovereignState(baseDir, state);
        failedDocs.push(doc);
        appendFailure(paths, `${doc.id} ${doc.name}: ${message}`);
      }
    }
    if (!allChunks.length) throw new Error("all_documents_failed");

    const embeddings = allChunks.map((chunk) => ({
      chunk_id: chunk.id,
      vector: embedText(chunk.text),
    }));
    const metadata = {
      version_id: versionId,
      generated_at: generatedAt,
      customer_id: customerId,
      doc_list_fingerprint: fingerprint,
      embedding_model: "local-hashing-embedding-v1",
      embedding_dimensions: EMBEDDING_DIMENSIONS,
      retrieval: {
        default_top_k: 5,
      },
      index: {
        kind: INDEX_KIND,
        metric: "cosine",
        faiss_factory: "Flat",
      },
      chunking: {
        min_tokens: MIN_CHUNK_TOKENS,
        target_tokens: TARGET_CHUNK_TOKENS,
        max_tokens: MAX_CHUNK_TOKENS,
        overlap_tokens: CHUNK_OVERLAP_TOKENS,
        max_collection_chunks: MAX_COLLECTION_CHUNKS,
      },
      documents: selectedDocs.map((doc) => ({
        id: doc.id,
        name: doc.name,
        sha256: doc.sha256,
        status: doc.status,
        failure_state: doc.failure_state,
        error: doc.error,
        chunks: doc.references,
      })),
      document_status: {
        total: selectedDocs.length,
        succeeded: publishedDocs.length,
        failed: failedDocs.length,
      },
      chunk_count: allChunks.length,
    };

    writeJsonl(path.join(bundleDir, "chunks.jsonl"), allChunks);
    writeJsonl(path.join(bundleDir, "embeddings.jsonl"), embeddings);
    writeJson(path.join(bundleDir, "metadata.json"), metadata);
    writeJson(path.join(bundleDir, "index.json"), {
      kind: INDEX_KIND,
      metric: "cosine",
      faiss_factory: "Flat",
      embedding_dimensions: EMBEDDING_DIMENSIONS,
      chunk_count: allChunks.length,
      vectors_file: "embeddings.jsonl",
      chunks_file: "chunks.jsonl",
      default_top_k: 5,
    });
    fs.writeFileSync(path.join(bundleDir, "wiki.md"), buildWiki(metadata, selectedDocs, allChunks));
    const zipPath = path.join(packageDir, `${versionId}.zip`);
    await zipDirectory(bundleDir, zipPath);
    const sizeBytes = fs.statSync(zipPath).size;
    if (sizeBytes > 500 * 1024 * 1024) throw new Error(`package_too_large:${sizeBytes}`);

    state = loadSovereignState(baseDir);
    for (const doc of state.documents) {
      const updated = selectedDocs.find((item) => item.id === doc.id);
      if (updated) Object.assign(doc, updated);
    }
    state.account.lastIndexedAt = generatedAt;
    state.account.version = versionId;
    state.account.docListFingerprint = fingerprint;
    state.account.packageUrl = `/fleet/api/sovereign/rag/packages/${encodeURIComponent(versionId)}/download`;
    state.account.lastError = null;
    state.packages.unshift({
      id: versionId,
      version_id: versionId,
      generated_at: generatedAt,
      customer_id: customerId,
      doc_list_fingerprint: fingerprint,
      chunk_count: allChunks.length,
      document_status: metadata.document_status,
      size_bytes: sizeBytes,
      download_url: state.account.packageUrl,
      local_path: zipPath,
    });
    saveSovereignState(baseDir, state);
    return { ok: true, metadata, package: state.packages[0], state };
  } catch (error) {
    state = loadSovereignState(baseDir);
    for (const doc of state.documents) {
      if (!doc.exclude && ["queued", "extracting_text", "chunking", "embedding"].includes(doc.status)) {
        doc.status = "failed";
        doc.error = error.message;
        doc.failure_state = "failed";
      }
    }
    state.account.lastError = error.message;
    state.notifications.unshift({
      id: stableId("notice", `${Date.now()}:${error.message}`),
      type: "rag_generation_failed",
      message: error.message,
      createdAt: new Date().toISOString(),
    });
    saveSovereignState(baseDir, state);
    appendFailure(paths, error.stack || error.message);
    throw error;
  }
}

export function retrieveFromIndex(packageDir, query, k = 5) {
  const limit = Math.max(1, Math.min(5, Number(k) || 5));
  const bundleDir = fs.existsSync(path.join(packageDir, "bundle")) ? path.join(packageDir, "bundle") : packageDir;
  const chunksPath = path.join(bundleDir, "chunks.jsonl");
  const embeddingsPath = path.join(bundleDir, "embeddings.jsonl");
  const chunks = fs.readFileSync(chunksPath, "utf8").trim().split("\n").filter(Boolean).map((line) => JSON.parse(line));
  const embeddings = new Map(
    fs.readFileSync(embeddingsPath, "utf8").trim().split("\n").filter(Boolean).map((line) => {
      const row = JSON.parse(line);
      return [row.chunk_id, row.vector];
    })
  );
  const queryEmbedding = embedText(query);
  return chunks
    .map((chunk) => ({ ...chunk, score: cosine(queryEmbedding, embeddings.get(chunk.id) || []) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}

export function resolvePackageZip(baseDir, versionId) {
  const safeVersion = String(versionId || "").replace(/[^A-Za-z0-9_.-]/g, "");
  if (!safeVersion) return null;
  const zipPath = path.join(getPaths(baseDir).packages, safeVersion, `${safeVersion}.zip`);
  return fs.existsSync(zipPath) ? zipPath : null;
}
