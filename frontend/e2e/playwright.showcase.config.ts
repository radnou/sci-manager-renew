import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './showcase/flows',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['html', { outputFolder: '../playwright-report/showcase' }], ['list']],
  outputDir: '../../marketing',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:5173',
    screenshot: 'on',
    video: 'on',
    viewport: { width: 1440, height: 900 },
    colorScheme: 'light',
    locale: 'fr-FR',
    timezoneId: 'Europe/Paris',
    actionTimeout: 15_000,
    navigationTimeout: 20_000,
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['iPhone 14'] } },
  ],
});
