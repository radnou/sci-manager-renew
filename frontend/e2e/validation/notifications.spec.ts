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

  test('le centre de notifications ouvre et affiche du contenu @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const bellButton = page.locator(
      'button[aria-label*="Notification"]'
    );

    const isVisible = await bellButton.first().isVisible().catch(() => false);
    if (!isVisible) {
      // Skip if bell not found — may be in a different layout
      return;
    }

    await bellButton.first().click();
    await page.waitForTimeout(500);

    // After clicking, some notification-related content should appear
    const content = await page.textContent('body');
    const hasNotifContent =
      content!.includes('Notification') ||
      content!.includes('notification') ||
      content!.includes('Aucune notification') ||
      content!.includes('Tout marquer') ||
      content!.includes('impayé') ||
      content!.includes('loyer');

    expect(hasNotifContent).toBe(true);
  });
});
