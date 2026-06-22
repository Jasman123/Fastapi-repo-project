const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: '.',
  timeout: 60_000,
  retries: 1,
  reporter: [
    ['html', { outputFolder: path.resolve(__dirname, '../../playwright-report/multi-doc-rag') }],
    ['list'],
  ],
  outputDir: path.resolve(__dirname, '../../test-results/multi-doc-rag'),

  use: {
    baseURL: 'http://localhost:8080',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'off',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
