/**
 * UI / e2e tests for the DocMind (multi-doc-rag) frontend.
 * API calls are intercepted via page.route() so tests run without
 * a real OpenAI key and with deterministic data.
 */
const { test, expect } = require('@playwright/test');
const path = require('path');

const SHOT = (name) =>
  path.resolve(__dirname, `../../screenshots/multi-doc-rag/${name}`);

// ── Shared mock data ──────────────────────────────────────────────────────────

const MOCK_STATUS_EMPTY = {
  status: 'ready',
  total_chunks: 0,
  document_count: 0,
  has_documents: false,
  documents: [],
};

const MOCK_STATUS_LOADED = {
  status: 'ready',
  total_chunks: 142,
  document_count: 1,
  has_documents: true,
  documents: [
    { document_id: 'doc_abc123', filename: 'Q4_Report.pdf', chunk_count: 142 },
  ],
};

const MOCK_QUERY_RESPONSE = {
  status: 'success',
  question: 'What are the key findings?',
  answer:
    'The document highlights three major findings: (1) Revenue grew 34% YoY, ' +
    '(2) Operating margins improved to 23.4%, and (3) Market expansion into ' +
    'Southeast Asia accelerated significantly in Q4.',
  sources: [
    {
      document_id: 'doc_abc123',
      filename: 'Q4_Report.pdf',
      page: 7,
      snippet:
        'Revenue grew 34% year-over-year, driven by enterprise contract expansions ' +
        'and new market penetration in Southeast Asia.',
      relevance_score: 0.0312,
    },
    {
      document_id: 'doc_abc123',
      filename: 'Q4_Report.pdf',
      page: 12,
      snippet:
        'Operating margins improved to 23.4% from 18.1% in the prior period, ' +
        'reflecting operational efficiency gains.',
      relevance_score: 0.0287,
    },
  ],
  model_used: 'gpt-4o-mini',
  total_chunks_searched: 142,
};

// ── Helper: mock a "connected" backend ────────────────────────────────────────

async function mockConnected(page, { status = MOCK_STATUS_EMPTY } = {}) {
  await page.route('**/health', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'ok' }) })
  );
  await page.route('**/ingest/status', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(status) })
  );
}

async function mockQuery(page) {
  await page.route('**/query/', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_QUERY_RESPONSE),
    })
  );
}

async function mockDemoMode(page) {
  // Return 503 to force the frontend into demo mode
  await page.route('**/health', (route) => route.fulfill({ status: 503 }));
}


// ── Page load ─────────────────────────────────────────────────────────────────

test.describe('UI — Page Load', () => {
  test('01 — page loads with correct title', async ({ page }) => {
    await mockConnected(page);
    await page.goto('/');
    await expect(page).toHaveTitle(/DocMind/i);
    await page.screenshot({ path: SHOT('01-page-load.png'), fullPage: true });
  });

  test('02 — key elements are visible on load', async ({ page }) => {
    await mockConnected(page);
    await page.goto('/');

    await expect(page.locator('#uploadBtn')).toBeVisible();
    await expect(page.locator('#queryInput')).toBeVisible();
    await expect(page.locator('#sendBtn')).toBeVisible();
    await expect(page.locator('#docList')).toBeVisible();
    await expect(page.locator('#statDocs')).toBeVisible();
    await expect(page.locator('#statChunks')).toBeVisible();
    await page.screenshot({ path: SHOT('02-elements.png'), fullPage: true });
  });

  test('03 — welcome screen visible before any query', async ({ page }) => {
    await mockConnected(page);
    await page.goto('/');
    await expect(page.locator('#welcome')).toBeVisible();
    await expect(page.locator('#welcome h1')).toContainText('documents');
    await page.screenshot({ path: SHOT('03-welcome.png'), fullPage: true });
  });

  test('04 — four suggestion chips are shown', async ({ page }) => {
    await mockConnected(page);
    await page.goto('/');
    await expect(page.locator('.chip')).toHaveCount(4);
    await page.screenshot({ path: SHOT('04-chips.png'), fullPage: true });
  });
});


// ── Connection status ─────────────────────────────────────────────────────────

test.describe('UI — Connection Status', () => {
  test('05 — shows "connected" when backend is reachable', async ({ page }) => {
    await mockConnected(page);
    await page.goto('/');
    await expect(page.locator('#statusText')).toContainText('connected', { timeout: 8_000 });
    await expect(page.locator('#statusDot')).not.toHaveClass(/offline/);
    await page.screenshot({ path: SHOT('05-connected.png'), fullPage: true });
  });

  test('06 — demo mode activates when backend is unreachable', async ({ page }) => {
    await mockDemoMode(page);
    await page.goto('/');
    await expect(page.locator('#demoBadge')).toBeVisible({ timeout: 8_000 });
    await expect(page.locator('#statusText')).toContainText('demo', { timeout: 8_000 });
    await page.screenshot({ path: SHOT('06-demo-mode.png'), fullPage: true });
  });

  test('07 — demo mode loads placeholder documents in sidebar', async ({ page }) => {
    await mockDemoMode(page);
    await page.goto('/');
    // Demo loads 3 fake documents
    await expect(page.locator('.doc-item')).toHaveCount(3, { timeout: 8_000 });
    await expect(page.locator('#statDocs')).toContainText('3');
    await page.screenshot({ path: SHOT('07-demo-sidebar.png'), fullPage: true });
  });
});


// ── Upload button ─────────────────────────────────────────────────────────────

test.describe('UI — Upload Button', () => {
  test('08 — upload button is disabled initially', async ({ page }) => {
    await mockConnected(page);
    await page.goto('/');
    await expect(page.locator('#uploadBtn')).toBeDisabled();
    await page.screenshot({ path: SHOT('08-upload-disabled.png'), fullPage: true });
  });
});


// ── Sidebar — loaded collection ───────────────────────────────────────────────

test.describe('UI — Sidebar with Documents', () => {
  test('09 — doc list shows documents from collection status', async ({ page }) => {
    await mockConnected(page, { status: MOCK_STATUS_LOADED });
    await page.goto('/');
    await expect(page.locator('.doc-item')).toHaveCount(1, { timeout: 5_000 });
    await expect(page.locator('.doc-name').first()).toContainText('Q4_Report.pdf');
    await page.screenshot({ path: SHOT('09-doc-list.png'), fullPage: true });
  });

  test('10 — stats reflect loaded collection', async ({ page }) => {
    await mockConnected(page, { status: MOCK_STATUS_LOADED });
    await page.goto('/');
    await expect(page.locator('#statDocs')).toContainText('1', { timeout: 5_000 });
    await expect(page.locator('#statChunks')).toContainText('142', { timeout: 5_000 });
    await page.screenshot({ path: SHOT('10-sidebar-docs.png'), fullPage: true });
  });
});


// ── Suggestion chips ──────────────────────────────────────────────────────────

test.describe('UI — Suggestion Chips', () => {
  test('11 — clicking a chip populates the query input', async ({ page }) => {
    await mockConnected(page);
    await page.goto('/');
    const chip = page.locator('.chip').first();
    const chipText = await chip.innerText();
    await chip.click();
    await expect(page.locator('#queryInput')).toHaveValue(chipText.trim());
    await page.screenshot({ path: SHOT('11-chip-selected.png'), fullPage: true });
  });

  test('12 — each chip text is distinct', async ({ page }) => {
    await mockConnected(page);
    await page.goto('/');
    const texts = await page.locator('.chip').allInnerTexts();
    const unique = new Set(texts.map((t) => t.trim()));
    expect(unique.size).toBe(4);
    await page.screenshot({ path: SHOT('12-chips-all.png'), fullPage: true });
  });
});


// ── Query flow ────────────────────────────────────────────────────────────────

test.describe('UI — Query Flow', () => {
  test('13 — send button submits query and hides welcome screen', async ({ page }) => {
    await mockConnected(page, { status: MOCK_STATUS_LOADED });
    await mockQuery(page);
    await page.goto('/');

    await page.locator('#queryInput').fill('What are the key findings?');
    await page.locator('#sendBtn').click();

    await expect(page.locator('#welcome')).not.toBeVisible({ timeout: 5_000 });
    await page.screenshot({ path: SHOT('13-query-sent.png'), fullPage: true });
  });

  test('14 — user message appears in chat after submit', async ({ page }) => {
    await mockConnected(page, { status: MOCK_STATUS_LOADED });
    await mockQuery(page);
    await page.goto('/');

    const QUESTION = 'What are the key findings?';
    await page.locator('#queryInput').fill(QUESTION);
    await page.locator('#sendBtn').click();

    await expect(page.locator('.message.user .msg-bubble').first())
      .toContainText(QUESTION, { timeout: 5_000 });
    await page.screenshot({ path: SHOT('14-user-message.png'), fullPage: true });
  });

  test('15 — assistant answer appears after response', async ({ page }) => {
    await mockConnected(page, { status: MOCK_STATUS_LOADED });
    await mockQuery(page);
    await page.goto('/');

    await page.locator('#queryInput').fill('What are the key findings?');
    await page.locator('#sendBtn').click();

    await expect(page.locator('.message.assistant .msg-bubble').first())
      .toContainText('Revenue grew', { timeout: 15_000 });
    await page.screenshot({ path: SHOT('15-answer.png'), fullPage: true });
  });

  test('16 — citation cards appear for each source', async ({ page }) => {
    await mockConnected(page, { status: MOCK_STATUS_LOADED });
    await mockQuery(page);
    await page.goto('/');

    await page.locator('#queryInput').fill('What are the key findings?');
    await page.locator('#sendBtn').click();

    await expect(page.locator('.citation-card')).toHaveCount(2, { timeout: 15_000 });
    await expect(page.locator('.citation-file').first()).toContainText('Q4_Report.pdf');
    await page.screenshot({ path: SHOT('16-citations.png'), fullPage: true });
  });

  test('17 — citation shows page number', async ({ page }) => {
    await mockConnected(page, { status: MOCK_STATUS_LOADED });
    await mockQuery(page);
    await page.goto('/');

    await page.locator('#queryInput').fill('What are the key findings?');
    await page.locator('#sendBtn').click();

    await expect(page.locator('.citation-page').first())
      .toContainText('p.7', { timeout: 15_000 });
    await page.screenshot({ path: SHOT('17-citation-page.png'), fullPage: true });
  });

  test('18 — query input is cleared after submit', async ({ page }) => {
    await mockConnected(page, { status: MOCK_STATUS_LOADED });
    await mockQuery(page);
    await page.goto('/');

    await page.locator('#queryInput').fill('What are the key findings?');
    await page.locator('#sendBtn').click();

    await expect(page.locator('.message.assistant .msg-bubble').first())
      .toBeVisible({ timeout: 15_000 });
    await expect(page.locator('#queryInput')).toHaveValue('');
    await page.screenshot({ path: SHOT('18-input-cleared.png'), fullPage: true });
  });
});


// ── Keyboard ──────────────────────────────────────────────────────────────────

test.describe('UI — Keyboard', () => {
  test('19 — Enter key submits query', async ({ page }) => {
    await mockConnected(page, { status: MOCK_STATUS_LOADED });
    await mockQuery(page);
    await page.goto('/');

    await page.locator('#queryInput').fill('What are the key findings?');
    await page.locator('#queryInput').press('Enter');

    await expect(page.locator('.message.user')).toBeVisible({ timeout: 5_000 });
    await page.screenshot({ path: SHOT('19-enter-submit.png'), fullPage: true });
  });

  test('20 — Shift+Enter adds a newline instead of submitting', async ({ page }) => {
    await mockConnected(page);
    await page.goto('/');

    await page.locator('#queryInput').fill('First line');
    await page.locator('#queryInput').press('Shift+Enter');

    // The user message list should still be empty (no submit happened)
    await expect(page.locator('.message.user')).toHaveCount(0);
    await page.screenshot({ path: SHOT('20-shift-enter.png'), fullPage: true });
  });
});


// ── Demo mode query ───────────────────────────────────────────────────────────

test.describe('UI — Demo Mode Query', () => {
  test('21 — query returns canned answer in demo mode', async ({ page }) => {
    await mockDemoMode(page);
    await page.goto('/');
    await expect(page.locator('#demoBadge')).toBeVisible({ timeout: 8_000 });

    await page.locator('#queryInput').fill('Summarize the key findings');
    await page.locator('#sendBtn').click();

    // Demo mode has a 1.4 s simulated delay; allow up to 10 s
    await expect(page.locator('.message.assistant .msg-bubble').first())
      .toBeVisible({ timeout: 10_000 });
    await page.screenshot({ path: SHOT('21-demo-answer.png'), fullPage: true });
  });
});
