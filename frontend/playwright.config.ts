import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,  // Sequential for screenshot consistency
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,  // Single worker for deterministic screenshots
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],
  outputDir: 'e2e-artifacts',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:5173',
    trace: 'on',
    screenshot: 'on',  // Capture screenshots on every test
    video: 'on',        // Record video of every test
    viewport: { width: 1440, height: 900 },
    locale: 'fr-FR',
    timezoneId: 'Europe/Paris',
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },
  projects: [
    {
      name: 'desktop-chrome',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 14'] },
    },
  ],
  // Don't auto-start webServer — user should start frontend+backend manually
  // Usage: cd frontend && pnpm dev   (terminal 1)
  //        cd backend && uvicorn app.main:app --reload  (terminal 2)
  //        cd frontend && pnpm exec playwright test     (terminal 3)
});
