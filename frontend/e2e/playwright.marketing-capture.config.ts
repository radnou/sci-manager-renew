import { defineConfig, devices } from '@playwright/test';

/**
 * Config for marketing video/screenshot capture.
 * Sequential, video ON, high quality, cookie banner dismissed.
 */
export default defineConfig({
  testDir: './validation',
  testMatch: 'billing-audit.spec.ts',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  outputDir: '../marketing/videos',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    screenshot: 'on',
    video: {
      mode: 'on',
      size: { width: 1440, height: 900 },
    },
    viewport: { width: 1440, height: 900 },
    locale: 'fr-FR',
    timezoneId: 'Europe/Paris',
    actionTimeout: 15_000,
    navigationTimeout: 20_000,
    launchOptions: {
      slowMo: 300, // Slow for readable demo videos
    },
  },
  projects: [
    { name: 'marketing', use: { ...devices['Desktop Chrome'] } },
  ],
});
