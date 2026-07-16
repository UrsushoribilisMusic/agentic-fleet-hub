import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const EMBEDDING_DIMENSIONS = 384;
const MIN_CHUNK_TOKENS = 512;
const TARGET_CHUNK_TOKENS = 768;
const MAX_CHUNK_TOKENS = 1024;
const CHUNK_OVERLAP_TOKENS = 80;

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
  const base = String(name || "document.pdf").replace(/[^\w .()-]/g, "_").trim();
  return base || "document.pdf";
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
    const fileName = `${id}.pdf`;
    const originalPath = path.join(paths.documents, fileName);
    if (pdfBytes?.length) fs.writeFileSync(originalPath, pdfBytes);
    const record = {
      id,
      name,
      size: Number(doc.size || pdfBytes?.length || 0),
      type: doc.type || "application/pdf",
      status: "pending",
      indexed: false,
      references: 0,
      exclude: false,
      notes: "",
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
    `# RAG Index Reference: ${metadata.customer_id}`,
    "",
    `Generated: ${metadata.generated_at}`,
    `Version: ${metadata.version_id}`,
    `Document fingerprint: ${metadata.doc_list_fingerprint}`,
    "",
    "## Sources",
    "",
  ];
  for (const doc of documents) {
    const docChunks = byDoc.get(doc.id) || [];
    lines.push(`### ${doc.name}`, "");
    lines.push(`- Document ID: \`${doc.id}\``);
    lines.push(`- SHA-256: \`${doc.sha256 || "unavailable"}\``);
    lines.push(`- Chunks: ${docChunks.length}`);
    if (doc.notes) lines.push(`- Admin notes: ${doc.notes}`);
    lines.push("");
    for (const chunk of docChunks) {
      lines.push(`#### ${chunk.id}`);
      lines.push("");
      lines.push(`Tokens: ${chunk.token_count}`);
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

function appendFailure(paths, message) {
  ensureDir(paths.logs);
  fs.appendFileSync(path.join(paths.logs, "rag-generation.log"), `${new Date().toISOString()} ${message}\n`);
}

export async function generateRagIndex(baseDir, options = {}) {
  const paths = getPaths(baseDir);
  let state = loadSovereignState(baseDir);
  const customerId = options.account_id || state.account.id || "corp-default";
  const selectedDocs = state.documents.filter((doc) => !doc.exclude);
  if (!selectedDocs.length) throw new Error("no_documents_selected");

  for (const doc of selectedDocs) {
    doc.status = "processing";
    doc.error = null;
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
    for (const doc of selectedDocs) {
      if (!doc.originalPath || !fs.existsSync(doc.originalPath)) {
        throw new Error(`missing_pdf:${doc.name}`);
      }
      const text = await extractPdfText(doc.originalPath);
      if (tokenize(text).length < 20) throw new Error(`pdf_text_extraction_failed:${doc.name}`);
      const chunks = chunkText(text, doc);
      doc.references = chunks.length;
      doc.indexed = true;
      doc.status = "ready";
      allChunks.push(...chunks);
    }

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
      chunking: {
        min_tokens: MIN_CHUNK_TOKENS,
        target_tokens: TARGET_CHUNK_TOKENS,
        max_tokens: MAX_CHUNK_TOKENS,
        overlap_tokens: CHUNK_OVERLAP_TOKENS,
      },
      documents: selectedDocs.map((doc) => ({
        id: doc.id,
        name: doc.name,
        sha256: doc.sha256,
        chunks: doc.references,
      })),
      chunk_count: allChunks.length,
    };

    writeJsonl(path.join(bundleDir, "chunks.jsonl"), allChunks);
    writeJsonl(path.join(bundleDir, "embeddings.jsonl"), embeddings);
    writeJson(path.join(bundleDir, "metadata.json"), metadata);
    fs.writeFileSync(path.join(bundleDir, "wiki.md"), buildWiki(metadata, selectedDocs, allChunks));
    const zipPath = path.join(packageDir, `${versionId}.zip`);
    await zipDirectory(bundleDir, zipPath);
    const sizeBytes = fs.statSync(zipPath).size;
    if (sizeBytes > 500 * 1024 * 1024) throw new Error(`package_too_large:${sizeBytes}`);

    state = loadSovereignState(baseDir);
    for (const doc of state.documents) {
      const updated = selectedDocs.find((item) => item.id === doc.id);
      if (updated) Object.assign(doc, {
        status: "ready",
        indexed: true,
        references: updated.references,
        error: null,
      });
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
      size_bytes: sizeBytes,
      download_url: state.account.packageUrl,
      local_path: zipPath,
    });
    saveSovereignState(baseDir, state);
    return { ok: true, metadata, package: state.packages[0], state };
  } catch (error) {
    state = loadSovereignState(baseDir);
    for (const doc of state.documents) {
      if (!doc.exclude && doc.status === "processing") {
        doc.status = "failed";
        doc.error = error.message;
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
    .slice(0, k);
}

export function resolvePackageZip(baseDir, versionId) {
  const safeVersion = String(versionId || "").replace(/[^A-Za-z0-9_.-]/g, "");
  if (!safeVersion) return null;
  const zipPath = path.join(getPaths(baseDir).packages, safeVersion, `${safeVersion}.zip`);
  return fs.existsSync(zipPath) ? zipPath : null;
}
