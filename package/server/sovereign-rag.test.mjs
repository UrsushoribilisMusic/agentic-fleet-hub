import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  addSovereignDocuments,
  generateRagIndex,
  loadSovereignState,
  retrieveFromIndex,
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
  assert.ok(result.package.size_bytes > 0);

  const packageDir = path.dirname(result.package.local_path);
  const hits = retrieveFromIndex(packageDir, "hydraulic pressure inspection", 3);
  assert.ok(hits.length > 0);
  assert.match(hits[0].text, /Hydraulic pressure inspection/i);

  const state = loadSovereignState(baseDir);
  assert.equal(state.documents[0].status, "ready");
  assert.ok(state.account.packageUrl.includes(result.metadata.version_id));
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
