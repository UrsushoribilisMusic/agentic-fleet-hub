'use strict';

function humanizeProcessingError(err) {
  const message = err && err.message ? String(err.message) : '';
  const lower = message.toLowerCase();

  if (lower.includes('enoent') || lower.includes('no such file')) {
    return 'The uploaded file could not be found. Please upload it again.';
  }
  if (lower.includes('encrypted') || lower.includes('password')) {
    return 'This document appears to be password-protected. Remove the password and upload it again.';
  }
  if (lower.includes('unsupported') || lower.includes('mime') || lower.includes('file type')) {
    return 'This file type is not supported yet. Please upload a PDF, text, or Markdown file.';
  }
  if (lower.includes('no text') || lower.includes('empty') || lower.includes('extract')) {
    return 'Canis could not extract readable text from this document.';
  }
  if (lower.includes('no wiki-ready documents')) {
    return 'No processed documents are ready to package yet.';
  }

  return 'Canis could not process this document. Please check the file and try again.';
}

function statusLabel(status) {
  switch (status) {
    case 'pending': return 'Queued';
    case 'extracting': return 'Extracting text';
    case 'chunked': return 'Building wiki pages';
    case 'wiki_ready': return 'Preparing knowledge pack';
    case 'packed': return 'Ready';
    case 'failed': return 'Failed';
    default: return 'Processing';
  }
}

module.exports = { humanizeProcessingError, statusLabel };
