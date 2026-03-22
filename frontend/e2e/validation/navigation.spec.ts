import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

test.describe('Navigation globale @P0', () => {

  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  test('le dashboard charge avec du contenu SCI @P0', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const content = await page.textContent('body');
    expect(content).toContain('Tableau de bord');
  });

  test('la navigation vers les finances fonctionne @P0', async ({ page }) => {
    await page.goto('/finances');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/finances');
  });

  test('les breadcrumbs affichent des noms lisibles @P1', async ({ page }) => {
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');

    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (await sciLink.isVisible().catch(() => false)) {
      await sciLink.click();
      await page.waitForLoadState('networkidle');

      const breadcrumbs = page.locator('nav[aria-label*="Ariane"]');
      if (await breadcrumbs.first().isVisible().catch(() => false)) {
        const text = await breadcrumbs.first().textContent();
        const uuidPattern = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
        expect(uuidPattern.test(text || '')).toBe(false);
      }
    }
  });

  test('la command palette (Cmd+K) ouvre @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await page.keyboard.press('Meta+k');
    await page.waitForTimeout(500);

    const commandPalette = page.locator('[role="dialog"], [cmdk-dialog]');
    let isVisible = await commandPalette.first().isVisible().catch(() => false);

    if (!isVisible) {
      await page.keyboard.press('Control+k');
      await page.waitForTimeout(500);
      isVisible = await commandPalette.first().isVisible().catch(() => false);
    }

    const searchInput = page.locator('[cmdk-input], input[placeholder*="chercher"]');
    const searchVisible = await searchInput.first().isVisible().catch(() => false);

    expect(isVisible || searchVisible).toBe(true);
  });
});
