import { defineConfig, devices } from '@playwright/test';

/**
 * Config for cinematic marketing demo capture.
 * Single continuous flow, slowMo for readable interactions.
 */
export default defineConfig({
  testDir: './showcase/flows',
  testMatch: '00-marketing-demo.spec.ts',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  timeout: 300_000, // 5min — long demo
  reporter: [['list']],
  outputDir: '../marketing/demo-output',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    screenshot: 'off', // We take manual screenshots
    video: 'off', // Video recorded via browser context in the test
    viewport: { width: 1440, height: 900 },
    locale: 'fr-FR',
    timezoneId: 'Europe/Paris',
    actionTimeout: 20_000,
    navigationTimeout: 30_000,
  },
  projects: [
    { name: 'demo', use: { ...devices['Desktop Chrome'] } },
  ],
});
