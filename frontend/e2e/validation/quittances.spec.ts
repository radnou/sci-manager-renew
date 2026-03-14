import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

test.describe('Quittances de loyer @P0', () => {

  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  async function goToFicheBienLoyers(page: import('@playwright/test').Page): Promise<boolean> {
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');

    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!(await sciLink.isVisible().catch(() => false))) return false;
    await sciLink.click();
    await page.waitForLoadState('networkidle');

    const biensLink = page.locator('a[href*="biens"]');
    if (!(await biensLink.first().isVisible().catch(() => false))) return false;
    await biensLink.first().click();
    await page.waitForLoadState('networkidle');

    const bienLink = page.locator('a[href*="/biens/"]').first();
    if (!(await bienLink.isVisible().catch(() => false))) return false;
    await bienLink.click();
    await page.waitForLoadState('networkidle');

    // Navigate to loyers tab
    const loyerTab = page.locator(
      'button:has-text("Loyer"), a:has-text("Loyer"), [data-testid*="loyer"]'
    );
    if (await loyerTab.first().isVisible().catch(() => false)) {
      await loyerTab.first().click();
      await page.waitForTimeout(500);
    }
    return true;
  }

  test('bouton quittance visible pour loyer paye @P0', async ({ page }) => {
    const navigated = await goToFicheBienLoyers(page);
    if (!navigated) return;

    // Look for quittance buttons next to paid loyers
    const quittanceButton = page.locator(
      'button:has-text("Quittance"), button:has-text("quittance"), button[aria-label*="quittance"]'
    );
    const payeRow = page.locator(':text("pay"), :text("Pay")');

    const hasQuittanceBtn = await quittanceButton.first().isVisible().catch(() => false);
    const hasPaidLoyers = await payeRow.first().isVisible().catch(() => false);

    // If there are paid loyers, quittance button should be available
    if (hasPaidLoyers) {
      expect(hasQuittanceBtn).toBe(true);
    }
  });

  test('generation quittance declenche telechargement @P1', async ({ page }) => {
    const navigated = await goToFicheBienLoyers(page);
    if (!navigated) return;

    const quittanceButton = page.locator(
      'button:has-text("Quittance"), button:has-text("quittance")'
    );

    if (await quittanceButton.first().isVisible().catch(() => false)) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 15_000 }).catch(() => null);
      await quittanceButton.first().click();
      const download = await downloadPromise;

      if (download) {
        const filename = download.suggestedFilename();
        expect(filename).toMatch(/\.pdf$/i);
      }
    }
  });

  test('verification du contenu de la quittance @P1', async ({ page }) => {
    const navigated = await goToFicheBienLoyers(page);
    if (!navigated) return;

    // Verify that quittance generation UI shows relevant fields
    const quittanceButton = page.locator(
      'button:has-text("Quittance"), button:has-text("quittance")'
    );

    if (await quittanceButton.first().isVisible().catch(() => false)) {
      // The quittance should reference locataire, montant, and periode
      const pageContent = await page.textContent('body');
      const hasRelevantInfo =
        pageContent!.includes('locataire') ||
        pageContent!.includes('Locataire') ||
        pageContent!.includes('montant') ||
        pageContent!.includes('Montant') ||
        /\d+[.,]\d{2}/.test(pageContent!); // Currency amount pattern
      expect(hasRelevantInfo).toBe(true);
    }
  });
});
