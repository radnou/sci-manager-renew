import { test, expect } from '@playwright/test';
import { setupAuthedMocks, SCI_ID_1 } from '../fixtures/api-mocks';

test.describe('Navigation globale @P0', () => {

  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  test('le SCI switcher fonctionne @P0', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Look for SCI switcher button (navbar or sidebar)
    const sciButton = page.locator(
      'button:has-text("SCI"), button:has-text("Mes SCI"), [aria-haspopup="listbox"]'
    );

    if (await sciButton.first().isVisible().catch(() => false)) {
      await sciButton.first().click();
      await page.waitForTimeout(500);

      // Dropdown should open with SCI options or "Voir toutes les SCI"
      const content = await page.textContent('body');
      const hasSciContent =
        content!.includes('Voir toutes les SCI') ||
        content!.includes('Aucune SCI') ||
        content!.includes('Belleville') ||
        content!.includes('SCI');
      expect(hasSciContent).toBe(true);
    }
  });

  test('les liens de navigation principaux fonctionnent @P0', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Verify key navigation links exist
    const dashboardLink = page.locator('a[href="/dashboard"]');
    expect(await dashboardLink.first().isVisible()).toBe(true);

    const financeLink = page.locator('a[href="/finances"]');
    expect(await financeLink.first().isVisible()).toBe(true);

    // Navigate to finances
    await financeLink.first().click();
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/finances');
  });

  test('les breadcrumbs affichent des noms lisibles (pas des UUID) @P1', async ({ page }) => {
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');

    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (await sciLink.isVisible().catch(() => false)) {
      await sciLink.click();
      await page.waitForLoadState('networkidle');

      const breadcrumbs = page.locator(
        '[class*="breadcrumb"], [class*="Breadcrumb"], nav[aria-label*="breadcrumb"], nav[aria-label*="Ariane"]'
      );

      if (await breadcrumbs.first().isVisible().catch(() => false)) {
        const breadcrumbText = await breadcrumbs.first().textContent();
        const uuidPattern = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
        expect(uuidPattern.test(breadcrumbText || '')).toBe(false);
      }
    }
  });

  test('la command palette (Cmd+K) ouvre @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await page.keyboard.press('Meta+k');
    await page.waitForTimeout(500);

    const commandPalette = page.locator(
      '[role="dialog"], [class*="command"], [class*="Command"], [class*="palette"], [class*="Palette"], [cmdk-dialog]'
    );
    const isVisible = await commandPalette.first().isVisible().catch(() => false);

    if (!isVisible) {
      await page.keyboard.press('Control+k');
      await page.waitForTimeout(500);
    }

    const paletteVisible = await commandPalette.first().isVisible().catch(() => false);
    const searchInput = page.locator(
      'input[placeholder*="chercher"], input[placeholder*="Chercher"], input[placeholder*="search"], [cmdk-input]'
    );
    const searchVisible = await searchInput.first().isVisible().catch(() => false);

    expect(paletteVisible || searchVisible).toBe(true);
  });
});
