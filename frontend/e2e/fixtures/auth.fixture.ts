import { test as base, type Page } from '@playwright/test';

// Check if auth credentials are available
export const hasAuth = () => !!process.env.E2E_AUTH_TOKEN;

// Fixture that injects auth session into the page
export const test = base.extend<{ authedPage: Page }>({
  authedPage: async ({ page }, use) => {
    if (!hasAuth()) {
      test.skip();
      return;
    }

    // Navigate to app first to set localStorage on correct origin
    await page.goto('/');

    // Inject fake Supabase session into localStorage
    const fakeSession = {
      access_token: process.env.E2E_AUTH_TOKEN,
      refresh_token: 'e2e-refresh-token',
      user: {
        id: process.env.E2E_USER_ID || 'e2e-user-id',
        email: process.env.E2E_USER_EMAIL || 'e2e@gerersci.fr',
        role: 'authenticated',
      },
      expires_at: Math.floor(Date.now() / 1000) + 3600,
    };

    await page.evaluate((session) => {
      localStorage.setItem('sb-auth-token', JSON.stringify(session));
      // Also set the app's own session key if it exists
      localStorage.setItem('gerersci.e2e-fake-session', JSON.stringify(session));
    }, fakeSession);

    // Reload to pick up session
    await page.reload();
    await page.waitForLoadState('networkidle');

    await use(page);
  },
});

export { expect } from '@playwright/test';

// Helper: take both viewport and full-page screenshots
export async function captureScreenshots(page: Page, name: string, dir = 'e2e-artifacts/screenshots') {
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500); // Let animations settle
  await page.screenshot({ path: `${dir}/${name}.png`, fullPage: false });
  await page.screenshot({ path: `${dir}/${name}-full.png`, fullPage: true });
}
