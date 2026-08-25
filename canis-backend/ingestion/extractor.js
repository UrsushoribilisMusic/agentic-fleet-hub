'use strict';

const fs = require('fs');
const path = require('path');

/**
 * Extract text and page count from a document file.
 * Supports: PDF (via pdf-parse), TXT, MD.
 * Falls back to raw UTF-8 bytes (truncated at 500 KB) for other types.
 *
 * Returns { text: string, pageCount: number }.
 */
async function extractText(filePath, filename) {
  const lower = (filename || '').toLowerCase();
  const raw = fs.readFileSync(filePath);

  if (lower.endsWith('.pdf')) {
    return extractPdf(raw);
  }

  if (lower.endsWith('.txt') || lower.endsWith('.md')) {
    const text = raw.toString('utf8');
    const pageCount = estimatePages(text);
    return { text, pageCount };
  }

  // Generic fallback: treat as UTF-8 text, cap at 500 KB
  const text = raw.slice(0, 500_000).toString('utf8');
  return { text, pageCount: estimatePages(text) };
}

async function extractPdf(rawBuffer) {
  let pdfParse;
  try {
    pdfParse = require('pdf-parse');
  } catch {
    throw new Error(
      'pdf-parse is not installed. Run: npm install pdf-parse'
    );
  }

  const data = await pdfParse(rawBuffer);
  return {
    text: data.text || '',
    pageCount: data.numpages || 0,
  };
}

// Approximate pages based on a standard 300-words-per-page ratio.
function estimatePages(text) {
  const words = text.split(/\s+/).filter((w) => w.length > 0).length;
  return Math.max(1, Math.ceil(words / 300));
}

module.exports = { extractText };
