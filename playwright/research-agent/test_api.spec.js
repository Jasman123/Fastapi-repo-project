const { test, expect } = require('@playwright/test');
const { API_KEY, BASE_URL } = require('../fixtures');

const HEADERS = { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' };
const VALID_TOPIC = 'Impact of AI on Southeast Asia 2025';

let savedJobId = null;

test.describe('API — Health', () => {
  test('GET /health returns ok', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/health`);
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('ok');
    expect(body).toHaveProperty('version');
    expect(body).toHaveProperty('db');
  });
});

test.describe('API — Research', () => {
  test('POST /research with valid topic returns completed report @slow', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/research`, {
      headers: HEADERS,
      data: { topic: VALID_TOPIC },
    });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('completed');
    expect(body).toHaveProperty('job_id');
    expect(body.topic).toBe(VALID_TOPIC);
    expect(body.report_markdown.length).toBeGreaterThan(100);
    expect(body.search_queries.length).toBeGreaterThan(0);
    savedJobId = body.job_id;
  });

  test('POST /research with invalid API key returns 401', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/research`, {
      headers: { 'X-API-Key': 'wrong-key', 'Content-Type': 'application/json' },
      data: { topic: VALID_TOPIC },
    });
    expect(res.status()).toBe(401);
  });

  test('POST /research with topic too short returns 422', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/research`, {
      headers: HEADERS,
      data: { topic: 'AI' },
    });
    expect(res.status()).toBe(422);
  });

  test('POST /research with missing topic returns 422', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/research`, {
      headers: HEADERS,
      data: {},
    });
    expect(res.status()).toBe(422);
  });
});

test.describe('API — Get Report', () => {
  test('GET /research/{job_id} returns 404 for unknown id', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/research/nonexistent-job-id-00000`, {
      headers: HEADERS,
    });
    expect(res.status()).toBe(404);
  });
});

test.describe('API — List Reports', () => {
  test('GET /research returns array', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/research`, { headers: HEADERS });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(Array.isArray(body)).toBe(true);
  });

  test('GET /research with limit param returns correct count', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/research?limit=2`, { headers: HEADERS });
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.length).toBeLessThanOrEqual(2);
  });
});
