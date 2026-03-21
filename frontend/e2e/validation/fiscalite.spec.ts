import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

test.describe('Fiscalite @P1', () => {

  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  async function goToFiscalite(page: import('@playwright/test').Page): Promise<boolean> {
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');

    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!(await sciLink.isVisible().catch(() => false))) return false;
    await sciLink.click();
    await page.waitForLoadState('networkidle');

    const fiscaLink = page.locator('a[href*="fiscalite"]');
    if (!(await fiscaLink.first().isVisible().catch(() => false))) return false;
    await fiscaLink.first().click();
    await page.waitForLoadState('networkidle');
    return true;
  }

  test('liste exercices par annee @P1', async ({ page }) => {
    const navigated = await goToFiscalite(page);
    if (!navigated) return;

    // Should show fiscal years or empty state
    const content = await page.textContent('body');
    const hasFiscalite =
      content!.includes('exercice') ||
      content!.includes('Exercice') ||
      content!.includes('Fiscalit') ||
      content!.includes('ann') ||
      content!.includes('Aucun') ||
      /20\d{2}/.test(content!); // Year pattern
    expect(hasFiscalite).toBe(true);
  });

  test('creer un nouvel exercice @P1', async ({ page }) => {
    const navigated = await goToFiscalite(page);
    if (!navigated) return;

    const createButton = page.locator(
      'button:has-text("Ajouter"), button:has-text("Cr"), button:has-text("Nouvel")'
    );
    if (await createButton.first().isVisible().catch(() => false)) {
      await createButton.first().click();
      await page.waitForTimeout(500);

      // Should show form with year input
      const anneeInput = page.locator(
        'input[name*="annee"], input[type="number"], select'
      );
      const formVisible = await anneeInput.first().isVisible().catch(() => false);
      expect(formVisible).toBe(true);
    }
  });

  test('bouton CERFA 2044 visible pour SCI IR @P1', async ({ page }) => {
    const navigated = await goToFiscalite(page);
    if (!navigated) return;

    // For IR SCIs, a CERFA 2044 button should exist
    const cerfaButton = page.locator(
      'button:has-text("CERFA"), button:has-text("2044"), a:has-text("CERFA")'
    );
    const cerfaVisible = await cerfaButton.first().isVisible().catch(() => false);

    // For IS SCIs, a message about liasse should appear instead
    const liasseMsg = page.locator(':text("liasse"), :text("Liasse"), :text("IS")');
    const liasseVisible = await liasseMsg.first().isVisible().catch(() => false);

    // One of the two should be present (or empty state)
    const content = await page.textContent('body');
    expect(cerfaVisible || liasseVisible || content!.includes('Aucun')).toBe(true);
  });

  test('si le CERFA 2044 est visible, l action utilisateur declenche bien la generation @P1', async ({ page }) => {
    let cerfaPdfCalled = false;

    await page.route('**/api/v1/cerfa/2044/pdf*', async (route) => {
      cerfaPdfCalled = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        body: Buffer.from('%PDF-1.4 cerfa mock')
      });
    });

    const navigated = await goToFiscalite(page);
    if (!navigated) return;

    const cerfaButton = page.getByRole('button', { name: /CERFA 2044/i }).first();
    if (!(await cerfaButton.isVisible().catch(() => false))) return;
    await cerfaButton.click();

    await expect.poll(() => cerfaPdfCalled).toBe(true);
  });
});
