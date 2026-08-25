'use strict';

const https = require('https');
const { v4: uuidv4 } = require('uuid');

const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || '';
const WIKI_MODEL = process.env.CANIS_WIKI_MODEL || 'claude-haiku-4-5-20251001';
const CHUNKS_PER_SECTION = 8;

/**
 * Generate wiki sections for a document from its chunks.
 * Groups chunks into batches of CHUNKS_PER_SECTION and calls Claude to
 * produce a (title, body) wiki section for each batch.
 *
 * If ANTHROPIC_API_KEY is absent, returns a stub section per batch so the
 * pipeline still runs end-to-end in environments without API access.
 *
 * @param {string} docId
 * @param {string} filename
 * @param {{ text: string }[]} chunks
 * @returns {Promise<{ id, doc_id, title, body, section_index, chunk_ids }[]>}
 */
async function generateWikiSections(docId, filename, chunks) {
  const batches = [];
  for (let i = 0; i < chunks.length; i += CHUNKS_PER_SECTION) {
    batches.push(chunks.slice(i, i + CHUNKS_PER_SECTION));
  }

  const sections = [];

  for (let batchIdx = 0; batchIdx < batches.length; batchIdx++) {
    const batch = batches[batchIdx];
    const chunkIds = batch.map((c) => c.id);
    const combinedText = batch.map((c) => c.text).join('\n\n');

    let title, body;

    if (ANTHROPIC_API_KEY) {
      try {
        ({ title, body } = await callClaude(filename, batchIdx + 1, batches.length, combinedText));
      } catch (err) {
        console.warn('[wiki] Claude call failed, using stub:', err.message);
        ({ title, body } = makeStubSection(filename, batchIdx + 1, batch));
      }
    } else {
      ({ title, body } = makeStubSection(filename, batchIdx + 1, batch));
    }

    sections.push({
      id: uuidv4(),
      doc_id: docId,
      title,
      body,
      section_index: batchIdx,
      chunk_ids: JSON.stringify(chunkIds),
      generated_at: new Date().toISOString(),
    });
  }

  return sections;
}

async function callClaude(filename, sectionNum, totalSections, text) {
  const prompt = [
    `You are organizing a document titled "${filename}" into a structured wiki.`,
    `This is section ${sectionNum} of ${totalSections}.`,
    '',
    'Given the following passage, produce:',
    '1. A short, descriptive section title (max 10 words).',
    '2. A concise wiki-style summary paragraph (3-6 sentences).',
    '',
    'Respond with JSON: {"title": "...", "body": "..."}',
    '',
    '--- PASSAGE ---',
    text.slice(0, 4000),
  ].join('\n');

  const responseText = await anthropicMessages([
    { role: 'user', content: prompt },
  ]);

  const match = responseText.match(/\{[\s\S]*\}/);
  if (!match) throw new Error('No JSON in Claude response');

  const parsed = JSON.parse(match[0]);
  if (!parsed.title || !parsed.body) throw new Error('Missing title or body in response');

  return { title: parsed.title, body: parsed.body };
}

function makeStubSection(filename, sectionNum, batch) {
  const firstWords = batch[0]
    ? batch[0].text.split(/\s+/).slice(0, 8).join(' ')
    : '';
  return {
    title: `Section ${sectionNum}: ${firstWords}…`,
    body: `[Wiki stub — section ${sectionNum} of document "${filename}". ` +
          `Contains ${batch.length} chunk(s). Set ANTHROPIC_API_KEY for full generation.]`,
  };
}

function anthropicMessages(messages) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: WIKI_MODEL,
      max_tokens: 512,
      messages,
    });

    const req = https.request(
      {
        hostname: 'api.anthropic.com',
        path: '/v1/messages',
        method: 'POST',
        headers: {
          'x-api-key': ANTHROPIC_API_KEY,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json',
          'content-length': Buffer.byteLength(body),
        },
      },
      (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => {
          try {
            const data = JSON.parse(Buffer.concat(chunks).toString());
            if (data.error) return reject(new Error(data.error.message || 'API error'));
            const text = (data.content || []).map((b) => b.text || '').join('');
            resolve(text);
          } catch (e) {
            reject(e);
          }
        });
      }
    );

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

module.exports = { generateWikiSections, CHUNKS_PER_SECTION };
