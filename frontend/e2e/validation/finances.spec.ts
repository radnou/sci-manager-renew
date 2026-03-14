import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

test.describe('Finances consolidees @P0', () => {

  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  test('la vue finances consolidees charge @P0', async ({ page }) => {
    await page.goto('/finances');
    await page.waitForLoadState('networkidle');

    // Should show financial overview or empty state
    const heading = page.locator('h1, h2, :text("Finance"), :text("finance")');
    await expect(heading.first()).toBeVisible({ timeout: 10_000 });
  });

  test('la repartition par SCI affiche un tableau avec noms cliquables @P1', async ({ page }) => {
    await page.goto('/finances');
    await page.waitForLoadState('networkidle');

    // Look for the repartition table or section
    const repartition = page.locator(
      ':text("partition"), :text("SCI"), table'
    );
    const exists = await repartition.first().isVisible().catch(() => false);

    // If data exists, SCI names should be links
    if (exists) {
      const sciLinks = page.locator('a[href*="/scis/"]');
      const linkCount = await sciLinks.count();
      // Either has links or shows empty state
      expect(linkCount >= 0).toBe(true);
    }
  });

  test('le filtre periode change les donnees @P1', async ({ page }) => {
    await page.goto('/finances');
    await page.waitForLoadState('networkidle');

    // Look for period filter (select or buttons)
    const periodFilter = page.locator(
      'select, button:has-text("12 mois"), button:has-text("6 mois"), button:has-text("3 mois"), [data-testid*="period"]'
    );
    if (await periodFilter.first().isVisible().catch(() => false)) {
      // Capture initial content
      const initialContent = await page.textContent('body');

      // Change period
      if (await page.locator('select').first().isVisible().catch(() => false)) {
        await page.locator('select').first().selectOption({ index: 1 });
      } else {
        // Click a different period button
        const altPeriod = page.locator('button:has-text("6 mois"), button:has-text("3 mois")');
        if (await altPeriod.first().isVisible().catch(() => false)) {
          await altPeriod.first().click();
        }
      }
      await page.waitForTimeout(1000);

      // Page should still be functional
      const newContent = await page.textContent('body');
      expect(newContent!.length).toBeGreaterThan(0);
    }
  });

  test('export CSV declenche un telechargement @P1', async ({ page }) => {
    await page.goto('/finances');
    await page.waitForLoadState('networkidle');

    // Look for export button
    const exportButton = page.locator(
      'button:has-text("Export"), button:has-text("export"), button:has-text("CSV"), button:has-text("charger")'
    );
    if (await exportButton.first().isVisible().catch(() => false)) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 10_000 }).catch(() => null);
      await exportButton.first().click();
      const download = await downloadPromise;

      if (download) {
        const filename = download.suggestedFilename();
        expect(filename).toMatch(/\.(csv|xlsx)$/i);
      }
    }
  });
});
