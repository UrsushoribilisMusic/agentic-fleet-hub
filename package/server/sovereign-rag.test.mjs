import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import {
  addSovereignDocuments,
  chunkText,
  generateRagIndex,
  getSovereignPersonas,
  loadSovereignConsoleState,
  loadSovereignState,
  retrieveFromIndex,
  resolvePackageZip,
} from "./sovereign-rag.mjs";

function makePdfLikeBuffer(text) {
  const escaped = text.replace(/[()\\]/g, "\\$&");
  return Buffer.from(`%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>
endobj
4 0 obj
<< /Length ${escaped.length + 32} >>
stream
BT
(${escaped}) Tj
ET
endstream
endobj
trailer
<< /Root 1 0 R >>
%%EOF
`);
}

function repeated(seed, count) {
  return Array.from({ length: count }, (_value, index) => `${seed} sentence ${index}.`).join(" ");
}

function makeDocxBuffer(text) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "sm-docx-"));
  const wordDir = path.join(tempDir, "word");
  fs.mkdirSync(wordDir, { recursive: true });
  fs.writeFileSync(path.join(tempDir, "[Content_Types].xml"), `<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>`);
  const escaped = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  fs.writeFileSync(path.join(wordDir, "document.xml"), `<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>${escaped}</w:t></w:r></w:p></w:body></w:document>`);
  const zipPath = path.join(os.tmpdir(), `sm-test-${Date.now()}-${Math.random().toString(16).slice(2)}.docx`);
  execFileSync("zip", ["-qr", zipPath, "."], { cwd: tempDir });
  const buffer = fs.readFileSync(zipPath);
  fs.rmSync(tempDir, { recursive: true, force: true });
  fs.rmSync(zipPath, { force: true });
  return buffer;
}

test("generates searchable RAG package from uploaded PDFs", async () => {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sm-rag-"));
  const pdfText = `${repeated("Pump safety lockout procedure", 360)} ${repeated("Hydraulic pressure inspection", 360)}`;
  addSovereignDocuments(baseDir, [
    {
      name: "Safety Handbook.pdf",
      size: pdfText.length,
      type: "application/pdf",
      contentBase64: makePdfLikeBuffer(pdfText).toString("base64"),
    },
  ]);

  const result = await generateRagIndex(baseDir, { account_id: "corp-test" });
  assert.equal(result.ok, true);
  assert.ok(result.metadata.chunk_count >= 1);
  assert.equal(result.metadata.embedding_dimensions, 384);
  assert.equal(result.metadata.index.kind, "faiss_flat");
  assert.equal(result.metadata.chunking.min_tokens, 256);
  assert.equal(result.metadata.chunking.max_tokens, 512);
  assert.equal(result.metadata.chunking.max_collection_chunks, 5000);
  assert.ok(result.package.size_bytes > 0);

  const packageDir = path.dirname(result.package.local_path);
  const hits = retrieveFromIndex(packageDir, "hydraulic pressure inspection", 3);
  assert.ok(hits.length > 0);
  assert.match(hits[0].text, /Hydraulic pressure inspection/i);

  const state = loadSovereignState(baseDir);
  assert.equal(state.documents[0].status, "published");
  assert.ok(state.account.packageUrl.includes(result.metadata.version_id));
});

test("chunks stay within SM-305 token bounds for long documents", () => {
  const chunks = chunkText(repeated("Calibration and lockout verification", 1500), {
    id: "manual",
    name: "Manual.txt",
  });
  assert.ok(chunks.length > 1);
  assert.ok(chunks.every((chunk) => chunk.token_count <= 512));
  assert.ok(chunks.slice(0, -1).every((chunk) => chunk.token_count >= 256));
});

test("publishes successful documents and surfaces scanned PDF failure per document", async () => {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sm-rag-"));
  addSovereignDocuments(baseDir, [
    {
      name: "Good Manual.txt",
      size: 4096,
      type: "text/plain",
      contentBase64: Buffer.from(repeated("Servo calibration torque sequence", 900)).toString("base64"),
    },
    {
      name: "Scanned Manual.pdf",
      size: 128,
      type: "application/pdf",
      contentBase64: Buffer.from("%PDF-1.4\n%%EOF\n").toString("base64"),
    },
  ]);

  const result = await generateRagIndex(baseDir, { account_id: "corp-test" });
  assert.equal(result.ok, true);
  assert.deepEqual(result.metadata.document_status, { total: 2, succeeded: 1, failed: 1 });
  assert.equal(result.metadata.documents.find((doc) => doc.name === "Scanned Manual.pdf").status, "needs_ocr");

  const state = loadSovereignState(baseDir);
  assert.equal(state.documents.find((doc) => doc.name === "Good Manual.txt").status, "published");
  const failed = state.documents.find((doc) => doc.name === "Scanned Manual.pdf");
  assert.equal(failed.status, "needs_ocr");
  assert.match(failed.error, /needs_ocr/);

  const bundleDir = path.join(path.dirname(result.package.local_path), "bundle");
  const wiki = fs.readFileSync(path.join(bundleDir, "wiki.md"), "utf8");
  assert.match(wiki, /failed document/);
  assert.match(wiki, /Scanned Manual\.pdf/);

  const hits = retrieveFromIndex(path.dirname(result.package.local_path), "servo calibration torque", 10);
  assert.ok(hits.length <= 5);
  assert.ok(hits.length > 0);
});

test("extracts DOCX documents into the same collection artifact path", async () => {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sm-rag-"));
  const docxText = repeated("Valve replacement procedure and seal inspection", 900);
  addSovereignDocuments(baseDir, [
    {
      name: "Maintenance Procedure.docx",
      size: docxText.length,
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      contentBase64: makeDocxBuffer(docxText).toString("base64"),
    },
  ]);

  const result = await generateRagIndex(baseDir, { account_id: "corp-test" });
  assert.equal(result.ok, true);
  assert.equal(result.metadata.document_status.failed, 0);
  const hits = retrieveFromIndex(path.dirname(result.package.local_path), "seal inspection", 3);
  assert.ok(hits.length > 0);
  assert.match(hits[0].text, /seal inspection/i);
});

test("different document sets produce distinct fingerprints and packages", async () => {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sm-rag-"));
  addSovereignDocuments(baseDir, [
    {
      name: "Alpha.pdf",
      size: 1024,
      type: "application/pdf",
      contentBase64: makePdfLikeBuffer(repeated("Alpha calibration manual", 700)).toString("base64"),
    },
  ]);
  const first = await generateRagIndex(baseDir, { account_id: "corp-test" });

  addSovereignDocuments(baseDir, [
    {
      name: "Beta.pdf",
      size: 1024,
      type: "application/pdf",
      contentBase64: makePdfLikeBuffer(repeated("Beta troubleshooting guide", 700)).toString("base64"),
    },
  ]);
  const second = await generateRagIndex(baseDir, { account_id: "corp-test" });

  assert.notEqual(first.metadata.doc_list_fingerprint, second.metadata.doc_list_fingerprint);
  assert.notEqual(first.package.local_path, second.package.local_path);
});

test("loads free example packages and preloaded personas", () => {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sm-rag-"));
  const state = loadSovereignConsoleState(baseDir);

  assert.equal(state.examples.length, 2);
  assert.deepEqual(state.examples.map((example) => example.id).sort(), [
    "industrial-troubleshooting",
    "robot-ross-atf",
  ]);
  for (const example of state.examples) {
    assert.equal(example.free, true);
    assert.equal(example.auth_required, false);
    assert.ok(example.download_url.includes("/fleet/api/sovereign/rag/packages/"));
    assert.ok(fs.existsSync(example.local_path));
    assert.equal(resolvePackageZip(baseDir, example.version_id), example.local_path);
  }

  const personas = getSovereignPersonas();
  assert.deepEqual(personas.map((persona) => persona.name), [
    "Field Engineer",
    "Product Manager",
    "Technical Writer",
  ]);
  assert.ok(personas.every((persona) => persona.system_prompt.includes("provided RAG context")));
});

test("example package is searchable with normal retrieval path", () => {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sm-rag-"));
  const state = loadSovereignConsoleState(baseDir);
  const industrial = state.examples.find((example) => example.id === "industrial-troubleshooting");
  assert.ok(industrial);

  const hits = retrieveFromIndex(path.dirname(industrial.local_path), "hydraulic pressure drift calibrated gauge", 3);
  assert.ok(hits.length > 0);
  assert.match(hits[0].text, /Hydraulic pressure|calibrated gauge/i);
});
