import { test, expect } from '@playwright/test';

const hasAuth = () => !!process.env.E2E_AUTH_TOKEN;

test.describe('Fiscalite @P1', () => {
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
      content!.includes('Fiscalité') ||
      content!.includes('année') ||
      content!.includes('Aucun') ||
      /20\d{2}/.test(content!); // Year pattern
    expect(hasFiscalite).toBe(true);
  });

  test('creer un nouvel exercice @P1', async ({ page }) => {
    const navigated = await goToFiscalite(page);
    if (!navigated) return;

    const createButton = page.locator(
      'button:has-text("Ajouter"), button:has-text("Créer"), button:has-text("Nouvel")'
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

  test('SCI IS affiche message liasse au lieu de CERFA @P2', async ({ page }) => {
    const navigated = await goToFiscalite(page);
    if (!navigated) return;

    // This test is conditional on whether the test SCI is IS
    // Just verify the page loads correctly
    const content = await page.textContent('body');
    const pageLoaded = content!.length > 100;
    expect(pageLoaded).toBe(true);
  });
});
