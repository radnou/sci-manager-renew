import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './validation',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : 4,
  reporter: [['html', { outputFolder: '../playwright-report/validation' }], ['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'off',
    trace: 'on-first-retry',
    locale: 'fr-FR',
    timezoneId: 'Europe/Paris',
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
