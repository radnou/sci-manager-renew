import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './production',
  fullyParallel: false,
  forbidOnly: true,
  retries: 1,
  workers: 1,
  reporter: [['html', { outputFolder: '../playwright-report/production' }], ['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'https://gerersci.fr',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    locale: 'fr-FR',
    timezoneId: 'Europe/Paris',
    actionTimeout: 15_000,
    navigationTimeout: 20_000
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } }
  ]
});
