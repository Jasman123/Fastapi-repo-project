/**
 * API-layer tests for multi-doc-rag.
 * All tests hit the real backend — none require an actual OpenAI call
 * (only validation endpoints are covered here).
 */
const { test, expect } = require('@playwright/test');

const BASE = 'http://localhost:8080';
const API  = `${BASE}/api/v1`;
const JSON_HDR = { 'Content-Type': 'application/json' };


// ── Health ────────────────────────────────────────────────────────────────────

test.describe('API — Health', () => {
  test('GET /health returns 200 with status ok', async ({ request }) => {
    const res = await request.get(`${BASE}/health`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('ok');
  });
});


// ── Ingest status ─────────────────────────────────────────────────────────────

test.describe('API — Ingest Status', () => {
  test('GET /ingest/status returns 200 with all required fields', async ({ request }) => {
    const res = await request.get(`${API}/ingest/status`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('status', 'ready');
    expect(body).toHaveProperty('total_chunks');
    expect(body).toHaveProperty('document_count');
    expect(body).toHaveProperty('has_documents');
    expect(body).toHaveProperty('documents');
    expect(typeof body.total_chunks).toBe('number');
    expect(typeof body.document_count).toBe('number');
    expect(typeof body.has_documents).toBe('boolean');
    expect(Array.isArray(body.documents)).toBe(true);
  });
});


// ── Query validation ──────────────────────────────────────────────────────────

test.describe('API — Query Validation', () => {
  test('POST /query/ with missing question returns 422', async ({ request }) => {
    const res = await request.post(`${API}/query/`, {
      headers: JSON_HDR,
      data: {},
    });
    expect(res.status()).toBe(422);
  });

  test('POST /query/ with question shorter than 3 chars returns 422', async ({ request }) => {
    const res = await request.post(`${API}/query/`, {
      headers: JSON_HDR,
      data: { question: 'Hi' },  // min_length = 3
    });
    expect(res.status()).toBe(422);
  });

  test('POST /query/ with question longer than 1000 chars returns 422', async ({ request }) => {
    const res = await request.post(`${API}/query/`, {
      headers: JSON_HDR,
      data: { question: 'x'.repeat(1001) },
    });
    expect(res.status()).toBe(422);
  });

  test('POST /query/ with top_k=0 returns 422', async ({ request }) => {
    const res = await request.post(`${API}/query/`, {
      headers: JSON_HDR,
      data: { question: 'What is the main topic?', top_k: 0 },
    });
    expect(res.status()).toBe(422);
  });

  test('POST /query/ with top_k=11 returns 422', async ({ request }) => {
    const res = await request.post(`${API}/query/`, {
      headers: JSON_HDR,
      data: { question: 'What is the main topic?', top_k: 11 },
    });
    expect(res.status()).toBe(422);
  });

  test('POST /query/ with empty collection returns 400', async ({ request }) => {
    // This test only passes deterministically when the collection is empty.
    // Skip if documents are already indexed.
    const status = await request.get(`${API}/ingest/status`);
    const { has_documents } = await status.json();
    test.skip(has_documents, 'Collection is non-empty — skip empty-collection guard test');

    const res = await request.post(`${API}/query/`, {
      headers: JSON_HDR,
      data: { question: 'What is this document about?' },
    });
    expect(res.status()).toBe(400);
    const body = await res.json();
    expect(body.detail).toMatch(/No documents/i);
  });
});


// ── Ingest validation ─────────────────────────────────────────────────────────

test.describe('API — Ingest Validation', () => {
  test('POST /ingest/ with no files returns 422', async ({ request }) => {
    const res = await request.post(`${API}/ingest/`);
    expect(res.status()).toBe(422);
  });

  test('POST /ingest/ with non-PDF content-type returns 415', async ({ request }) => {
    const res = await request.post(`${API}/ingest/`, {
      multipart: {
        files: {
          name: 'document.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from('This is plain text, not a PDF.'),
        },
      },
    });
    expect(res.status()).toBe(415);
  });

  test('POST /ingest/ with empty PDF returns 400', async ({ request }) => {
    const res = await request.post(`${API}/ingest/`, {
      multipart: {
        files: {
          name: 'empty.pdf',
          mimeType: 'application/pdf',
          buffer: Buffer.from(''),
        },
      },
    });
    expect(res.status()).toBe(400);
  });

  test('POST /ingest/ with oversized file returns 413', async ({ request }) => {
    const res = await request.post(`${API}/ingest/`, {
      multipart: {
        files: {
          name: 'huge.pdf',
          mimeType: 'application/pdf',
          buffer: Buffer.alloc(51 * 1024 * 1024, 0x25), // 51 MB
        },
      },
    });
    expect(res.status()).toBe(413);
  });
});
