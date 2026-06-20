const { test, expect } = require('@playwright/test');
const path = require('path');
const { switchProvider, screenshotDir } = require('../../fixtures');

const BASE_URL = 'http://localhost:8001';
const API_KEY = 'dev-key-change-me';
const HEADERS = { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' };
const TOPIC = 'Impact of generative AI on Indonesia economy 2025';

// ── OpenAI Provider ──────────────────────────────────────────────────────────
test.describe('Provider: OpenAI @slow', () => {
  test.setTimeout(150_000);

  test.beforeAll(() => {
    switchProvider('openai');
  });

  test('health check passes after switch', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/health`);
    expect(res.status()).toBe(200);
    expect((await res.json()).status).toBe('ok');
  });

  test('research completes and log shows OpenAI provider', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-url-input').fill(BASE_URL);
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();

    await expect(page.locator('#meta-status')).toContainText('completed', { timeout: 130_000 });

    const queriesText = await page.locator('#meta-queries').innerText();
    expect(parseInt(queriesText)).toBeGreaterThan(0);

    const sourcesText = await page.locator('#meta-sources').innerText();
    expect(parseInt(sourcesText)).toBeGreaterThan(0);

    await page.screenshot({
      path: path.join(screenshotDir('openai'), 'result-report.png'),
      fullPage: true,
    });
  });

  test('API returns completed report with OpenAI @slow', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/research`, {
      headers: HEADERS,
      data: { topic: TOPIC },
    });
    expect(res.status()).toBe(200);
    const body = await res.json();

    expect(body.status).toBe('completed');
    expect(body.report_markdown).toMatch(/^#/m);
    expect(body.sources_count).toBeGreaterThan(0);
    expect(body.elapsed_seconds).toBeGreaterThan(0);
    expect(body.search_queries.length).toBeGreaterThan(0);
  });

  test('queries tab shows results', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-url-input').fill(BASE_URL);
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();
    await expect(page.locator('#meta-status')).toContainText('completed', { timeout: 130_000 });

    await page.locator('.tab-btn', { hasText: /queries/i }).click();
    await page.screenshot({
      path: path.join(screenshotDir('openai'), 'result-queries.png'),
      fullPage: true,
    });
  });

  test('sources tab shows source cards', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-url-input').fill(BASE_URL);
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();
    await expect(page.locator('#meta-status')).toContainText('completed', { timeout: 130_000 });

    await page.locator('.tab-btn', { hasText: /sources/i }).click();
    await page.screenshot({
      path: path.join(screenshotDir('openai'), 'result-sources.png'),
      fullPage: true,
    });
  });
});

// ── Local LLM (llama.cpp) Provider ──────────────────────────────────────────
test.describe('Provider: Local llama.cpp @slow', () => {
  test.setTimeout(180_000);

  test.beforeAll(() => {
    switchProvider('local');
  });

  test('health check passes after switch to local', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/health`);
    expect(res.status()).toBe(200);
    expect((await res.json()).status).toBe('ok');
  });

  test('research completes with local LLM and shows report', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-url-input').fill(BASE_URL);
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();

    await expect(page.locator('#meta-status')).toContainText('completed', { timeout: 160_000 });

    const queriesText = await page.locator('#meta-queries').innerText();
    expect(parseInt(queriesText)).toBeGreaterThan(0);

    await page.screenshot({
      path: path.join(screenshotDir('local'), 'result-report.png'),
      fullPage: true,
    });
  });

  test('API returns completed report with local LLM @slow', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/research`, {
      headers: HEADERS,
      data: { topic: TOPIC },
    });
    expect(res.status()).toBe(200);
    const body = await res.json();

    expect(body.status).toBe('completed');
    expect(body.report_markdown).toMatch(/^#/m);
    expect(body.elapsed_seconds).toBeGreaterThan(0);
    expect(body.search_queries.length).toBeGreaterThan(0);
  });

  test('queries tab shows results for local LLM', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-url-input').fill(BASE_URL);
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();
    await expect(page.locator('#meta-status')).toContainText('completed', { timeout: 160_000 });

    await page.locator('.tab-btn', { hasText: /queries/i }).click();
    await page.screenshot({
      path: path.join(screenshotDir('local'), 'result-queries.png'),
      fullPage: true,
    });
  });

  test('sources tab shows source cards for local LLM', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-url-input').fill(BASE_URL);
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();
    await expect(page.locator('#meta-status')).toContainText('completed', { timeout: 160_000 });

    await page.locator('.tab-btn', { hasText: /sources/i }).click();
    await page.screenshot({
      path: path.join(screenshotDir('local'), 'result-sources.png'),
      fullPage: true,
    });
  });
});
