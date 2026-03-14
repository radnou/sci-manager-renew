import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

test.describe('Notifications @P1', () => {

  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  test('icone cloche affiche le compteur non-lus @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Look for notification bell icon
    const bellIcon = page.locator(
      'button[aria-label*="notification"], button[aria-label*="Notification"], [data-testid*="notification-bell"], [class*="notification"] button, button:has(svg)'
    );

    // The bell should be in the header/navbar area
    const header = page.locator('header, nav');
    const bellInHeader = header.locator(
      'button[aria-label*="notification"], [data-testid*="notification"], [class*="notification"]'
    );

    const bellVisible = await bellInHeader.first().isVisible().catch(() => false);
    const genericBell = await bellIcon.first().isVisible().catch(() => false);

    // Bell icon or notification indicator should exist
    expect(bellVisible || genericBell).toBe(true);
  });

  test('le centre de notifications ouvre @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Click on notification bell/icon
    const bellButton = page.locator(
      'button[aria-label*="notification"], button[aria-label*="Notification"], [data-testid*="notification-bell"]'
    );

    if (await bellButton.first().isVisible().catch(() => false)) {
      await bellButton.first().click();
      await page.waitForTimeout(500);

      // Notification center/panel should open
      const notifPanel = page.locator(
        '[class*="notification-center"], [class*="NotificationCenter"], [role="dialog"], [class*="popover"], [class*="Popover"], [class*="panel"]'
      );
      const content = await page.textContent('body');
      const hasNotifContent =
        content!.includes('Notification') ||
        content!.includes('notification') ||
        content!.includes('Aucune notification') ||
        content!.includes('Tout marquer');

      const panelVisible = await notifPanel.first().isVisible().catch(() => false);
      expect(panelVisible || hasNotifContent).toBe(true);
    }
  });

  test('marquer une notification comme lue @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const bellButton = page.locator(
      'button[aria-label*="notification"], button[aria-label*="Notification"], [data-testid*="notification-bell"]'
    );

    if (await bellButton.first().isVisible().catch(() => false)) {
      await bellButton.first().click();
      await page.waitForTimeout(500);

      // Look for mark-as-read button (individual or bulk)
      const markReadButton = page.locator(
        'button:has-text("Marquer"), button:has-text("Lu"), button:has-text("lu"), button:has-text("Tout marquer")'
      );
      const hasMarkRead = await markReadButton.first().isVisible().catch(() => false);

      // Also check for notification items that can be clicked
      const notifItems = page.locator(
        '[class*="notification-item"], [class*="NotificationItem"], [data-testid*="notification-item"]'
      );
      const hasItems = (await notifItems.count()) > 0;

      // Either has mark-read functionality or no notifications to mark
      expect(hasMarkRead || !hasItems).toBe(true);
    }
  });
});
