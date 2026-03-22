import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

test.describe('Notifications @P1', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  test('une icone de notification est visible @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Look for notification bell in navbar or sidebar
    const bellButton = page.locator(
      'button[aria-label*="Notification"], button:has-text("Notification")'
    );

    // Also check for bell icon in header
    const bellInHeader = page.locator(
      'nav button[aria-label*="Notification"], header button[aria-label*="Notification"]'
    );

    const bellVisible = await bellButton.first().isVisible().catch(() => false);
    const headerBell = await bellInHeader.first().isVisible().catch(() => false);

    expect(bellVisible || headerBell).toBe(true);
  });

  test('le centre de notifications est accessible @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Notification bell should be present somewhere (navbar or sidebar)
    const bellButton = page.locator('button[aria-label*="Notification"]');
    const notifText = page.locator(':text("Notification")');

    const bellVisible = await bellButton.first().isVisible().catch(() => false);
    const textVisible = await notifText.first().isVisible().catch(() => false);

    expect(bellVisible || textVisible).toBe(true);
  });
});
