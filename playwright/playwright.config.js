const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: '.',
  timeout: 120_000,
  retries: 1,
  reporter: [['html', { outputFolder: '../playwright-report' }], ['list']],
  outputDir: '../test-results',

  use: {
    baseURL: 'http://localhost:8001',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'off',
  },

  projects: [
    {
      name: 'openai',
      use: {
        ...devices['Desktop Chrome'],
        extraHTTPHeaders: { 'X-API-Key': 'dev-key-change-me' },
      },
    },
    {
      name: 'local',
      use: {
        ...devices['Desktop Chrome'],
        extraHTTPHeaders: { 'X-API-Key': 'dev-key-change-me' },
      },
    },
  ],
});
