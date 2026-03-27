import { defineConfig, devices } from '@playwright/test';

const AUTH_FILE = 'e2e-artifacts/.auth/session.json';

export default defineConfig({
  testDir: './production',
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: [['html', { outputFolder: '../playwright-report/local' }], ['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5174',
    screenshot: 'only-on-failure',
    video: process.env.E2E_VIDEO === 'on' ? 'on' : 'retain-on-failure',
    trace: 'retain-on-failure',
    locale: 'fr-FR',
    timezoneId: 'Europe/Paris',
    actionTimeout: 15_000,
    navigationTimeout: 20_000
  },
  projects: [
    // Setup: login once and save session
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },
    // Tests: use saved session state
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: AUTH_FILE,
      },
      dependencies: ['setup'],
      testIgnore: /auth\.setup\.ts/,
    }
  ]
});
