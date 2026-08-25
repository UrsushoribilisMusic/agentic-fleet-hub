'use strict';

const { v4: uuidv4 } = require('uuid');

const CHUNK_WORDS = 200;
const OVERLAP_WORDS = 20;

/**
 * Split text into overlapping ~200-word segments with 20-word overlap.
 * Each chunk gets a stable UUID and a TF-IDF term frequency map.
 *
 * @param {string} text
 * @param {string} docId
 * @param {string} filename
 * @returns {{ id, doc_id, text, source_page, chunk_index, word_count, chunk_type, tfidf_json }[]}
 */
function chunkText(text, docId, filename) {
  const words = text.split(/\s+/).filter((w) => w.length > 0);
  if (words.length === 0) return [];

  const step = CHUNK_WORDS - OVERLAP_WORDS;
  const chunks = [];
  let chunkIndex = 0;

  for (let i = 0; i < words.length; i += step) {
    const slice = words.slice(i, i + CHUNK_WORDS);
    const chunkText = slice.join(' ');
    const tf = computeTf(slice);

    chunks.push({
      id: uuidv4(),
      doc_id: docId,
      text: chunkText,
      source_page: filename,
      chunk_index: chunkIndex++,
      word_count: slice.length,
      chunk_type: 'document_text',
      tfidf_json: JSON.stringify(tf),
    });

    if (i + CHUNK_WORDS >= words.length) break;
  }

  return chunks;
}

/**
 * Compute term frequency (TF) map for a word array.
 * Stop words are excluded. Values are normalized (count / total).
 */
function computeTf(words) {
  const tf = {};
  const filtered = words.map((w) => w.toLowerCase().replace(/[^a-z0-9]/g, ''))
    .filter((w) => w.length > 2 && !STOP_WORDS.has(w));

  if (filtered.length === 0) return tf;

  for (const w of filtered) {
    tf[w] = (tf[w] || 0) + 1;
  }
  for (const k of Object.keys(tf)) {
    tf[k] = tf[k] / filtered.length;
  }
  return tf;
}

const STOP_WORDS = new Set([
  'the','and','for','are','but','not','you','all','can','had','her','was',
  'one','our','out','day','get','has','him','his','how','its','let','man',
  'new','now','old','see','two','way','who','boy','did','its','let','put',
  'say','she','too','use','with','that','have','this','will','your','from',
  'they','know','want','been','good','much','some','time','very','when',
  'come','here','just','like','long','make','many','more','only','over',
  'such','take','than','them','well','were',
]);

module.exports = { chunkText, CHUNK_WORDS, OVERLAP_WORDS };
