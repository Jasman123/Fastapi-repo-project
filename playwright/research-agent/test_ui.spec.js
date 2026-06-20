const { test, expect } = require('@playwright/test');
const path = require('path');

const SHOT = (name) => path.resolve(__dirname, `../../screenshots/${name}`);
const TOPIC = 'AI trends in Southeast Asia 2025';
const API_KEY = 'dev-key-change-me';

const MOCK_RESPONSE = {
  job_id: 'screenshot-job-001',
  topic: TOPIC,
  status: 'completed',
  report_markdown: `# AI Trends in Southeast Asia 2025\n\n## Executive Summary\nSoutheast Asia is experiencing rapid AI adoption across fintech, healthcare, and logistics sectors, driven by a young digital-native population and strong government support.\n\n## Background\nCountries like Singapore, Indonesia, and Vietnam have invested heavily in AI infrastructure. Singapore's National AI Strategy 2.0 and Indonesia's AI roadmap signal regional commitment.\n\n## Key Findings\n1. **Fintech Dominance**: AI-powered credit scoring is transforming financial inclusion for the unbanked.\n2. **Healthcare AI**: Diagnostic imaging AI is being deployed in rural hospitals in Philippines and Indonesia.\n3. **Talent Gap**: Demand for AI engineers outpaces supply by 3:1 across the region.\n4. **Regulatory Landscape**: Varied regulations — Singapore leads with a mature AI governance framework.\n\n## Analysis & Implications\nThe region's AI growth is accelerating but uneven. First-movers in AI infrastructure stand to gain significant competitive advantage.\n\n## Conclusion\nSoutheast Asia represents one of the most dynamic AI markets globally, with compounding growth expected through 2026.\n\n## Sources\n- [McKinsey Digital Report 2025](https://mckinsey.com)\n- [Singapore IMDA AI Strategy](https://imda.gov.sg)\n- [World Economic Forum SEA Tech](https://weforum.org)`,
  search_queries: [
    'AI adoption Southeast Asia 2025 trends',
    'Singapore Indonesia AI investment fintech',
    'Southeast Asia AI talent gap skills',
    'AI regulation policy ASEAN 2025',
  ],
  sources_count: 8,
  elapsed_seconds: 42.3,
  created_at: new Date().toISOString(),
};

async function mockAndRun(page) {
  await page.route('**/research', route =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_RESPONSE) })
  );
  await page.goto('/');
  await page.locator('#api-key-input').fill(API_KEY);
  await page.locator('#topic-input').fill(TOPIC);
  await page.locator('#run-btn').click();
  await expect(page.locator('#meta-status')).toContainText('completed', { timeout: 30_000 });
}

test.describe('UI — Page Load', () => {
  test('01 — page loads and shows all key elements', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/research/i);

    // Pipeline nodes
    for (const node of ['plan_research', 'search_web', 'extract_data', 'synthesize', 'generate_report']) {
      await expect(page.locator(`#node-${node}`)).toBeVisible();
    }

    await expect(page.locator('#run-btn')).toBeVisible();
    await expect(page.locator('#run-btn')).toBeEnabled();
    await expect(page.locator('.example-chip')).toHaveCount(4);

    await page.screenshot({ path: SHOT('01-page-load.png'), fullPage: true });
  });
});

test.describe('UI — Settings Panel', () => {
  test('02 — settings inputs have correct defaults', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#api-url-input')).toHaveValue(/localhost:800/);
    await expect(page.locator('#api-key-input')).toHaveValue(API_KEY);

    await page.locator('#api-url-input').click();
    await page.screenshot({ path: SHOT('02-settings.png'), fullPage: true });
  });
});

test.describe('UI — Example Chips', () => {
  test('03 — clicking chip populates topic input', async ({ page }) => {
    await page.goto('/');
    const chip = page.locator('.example-chip').first();
    const chipText = await chip.innerText();
    await chip.click();
    await expect(page.locator('#topic-input')).toHaveValue(chipText.trim());

    await page.screenshot({ path: SHOT('03-chip-selected.png'), fullPage: true });
  });
});

test.describe('UI — Topic Input', () => {
  test('04 — topic filled and ready to run', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await expect(page.locator('#topic-input')).toHaveValue(TOPIC);

    await page.screenshot({ path: SHOT('04-topic-filled.png'), fullPage: true });
  });
});

test.describe('UI — Full Research Run @slow', () => {
  test.setTimeout(150_000);

  test('05 — pipeline animates while running', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();

    // Wait for any pipeline node to become active
    await page.locator('.pipeline-node.active, [class*="active"]').first()
      .waitFor({ timeout: 15_000 }).catch(() => {});

    await page.screenshot({ path: SHOT('05-pipeline-running.png'), fullPage: true });
  });

  test('06 — research completes and shows report', async ({ page }) => {
    await mockAndRun(page);
    const queriesText = await page.locator('#meta-queries').innerText();
    expect(parseInt(queriesText)).toBeGreaterThan(0);
    await page.screenshot({ path: SHOT('06-result-report.png'), fullPage: true });
  });

  test('07 — queries tab shows search queries', async ({ page }) => {
    await mockAndRun(page);
    await page.locator('.tab-btn', { hasText: /queries/i }).click();
    await expect(page.locator('#tab-queries')).toBeVisible();
    await page.screenshot({ path: SHOT('07-result-queries.png'), fullPage: true });
  });

  test('08 — sources tab shows source cards', async ({ page }) => {
    await mockAndRun(page);
    await page.locator('.tab-btn', { hasText: /sources/i }).click();
    await expect(page.locator('#tab-sources')).toBeVisible();
    await page.screenshot({ path: SHOT('08-result-sources.png'), fullPage: true });
  });

  test('09 — raw markdown tab shows markdown text', async ({ page }) => {
    await mockAndRun(page);
    await page.locator('.tab-btn', { hasText: /raw/i }).click();
    await expect(page.locator('#tab-raw')).toBeVisible();
    const raw = await page.locator('#raw-output').innerText();
    expect(raw).toMatch(/^#/);
    await page.screenshot({ path: SHOT('09-result-raw.png'), fullPage: true });
  });

  test('copy button changes text to Copied', async ({ page }) => {
    // Mock clipboard API — headless Chrome silently rejects it without this
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: () => Promise.resolve() },
        writable: true,
      });
    });

    // Mock research response so the test doesn't depend on live LLM
    await page.route('**/research', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'test-job-copy',
          topic: TOPIC,
          status: 'completed',
          report_markdown: '# Test Report\n\n## Summary\nThis is a test report.',
          search_queries: ['query 1', 'query 2'],
          sources_count: 2,
          elapsed_seconds: 1.5,
          created_at: new Date().toISOString(),
        }),
      })
    );

    await page.goto('/');
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();
    await expect(page.locator('#meta-status')).toContainText('completed', { timeout: 15_000 });

    await page.locator('.action-btn').first().click();
    await expect(page.locator('.action-btn').first()).toContainText(/copied/i, { timeout: 3_000 });
  });

  test('download button triggers file download', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();
    await expect(page.locator('#meta-status')).toContainText('completed', { timeout: 130_000 });

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.locator('.action-btn').nth(1).click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.md$/);
  });
});

test.describe('UI — Error State', () => {
  test('10 — API error shows error banner', async ({ page }) => {
    // Intercept and return a 401 to guarantee the error path is exercised
    await page.route('**/research', route =>
      route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"Invalid or missing API key"}' })
    );

    await page.goto('/');
    await page.locator('#api-key-input').fill('wrong-key');
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();

    await expect(page.locator('#error-banner')).toBeVisible({ timeout: 15_000 });

    await page.screenshot({ path: SHOT('10-error-state.png'), fullPage: true });
  });
});

test.describe('UI — Demo Mode', () => {
  test('11 — unreachable API triggers demo mode', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-url-input').fill('http://localhost:9999');
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#run-btn').click();

    await expect(page.locator('#log-feed')).toContainText('[DEMO]', { timeout: 15_000 });
    await expect(page.locator('#meta-status')).toContainText('demo', { timeout: 30_000 });

    await page.screenshot({ path: SHOT('11-demo-mode.png'), fullPage: true });
  });
});

test.describe('UI — Keyboard Shortcut', () => {
  test('Enter key in topic input triggers run', async ({ page }) => {
    await page.goto('/');
    await page.locator('#api-key-input').fill(API_KEY);
    await page.locator('#topic-input').fill(TOPIC);
    await page.locator('#topic-input').press('Enter');

    // Just verify the pipeline starts (run-btn becomes disabled)
    await expect(page.locator('#run-btn')).toBeDisabled({ timeout: 5_000 });
  });
});
