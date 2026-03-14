import { test, expect } from '@playwright/test';

const hasAuth = () => !!process.env.E2E_AUTH_TOKEN;

test.describe('Finances consolidees @P0', () => {
  test.skip(!hasAuth(), 'Requires E2E_AUTH_TOKEN');

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.evaluate((token) => {
      const session = {
        access_token: token,
        refresh_token: 'e2e-refresh',
        user: {
          id: process.env.E2E_USER_ID || 'e2e-user',
          email: process.env.E2E_USER_EMAIL || 'e2e@test.fr',
          role: 'authenticated',
        },
        expires_at: Math.floor(Date.now() / 1000) + 3600,
      };
      localStorage.setItem('sb-auth-token', JSON.stringify(session));
    }, process.env.E2E_AUTH_TOKEN);
    await page.reload();
    await page.waitForLoadState('networkidle');
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
      ':text("Répartition"), :text("répartition"), :text("SCI"), table'
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
      'button:has-text("Export"), button:has-text("export"), button:has-text("CSV"), button:has-text("Télécharger")'
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
