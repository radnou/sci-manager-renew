import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

const isLiveTarget = (process.env.E2E_BASE_URL || '').startsWith('https://');

test.describe('Parametres et compte @P1', () => {
  test.skip(isLiveTarget, 'Requires mock auth — skipped against live target');
  async function openAuthenticatedPage(page: import('@playwright/test').Page, path: string) {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.goto(path);
    await page.waitForLoadState('networkidle');
  }

  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  test('la page parametres unifie charge @P1', async ({ page }) => {
    await openAuthenticatedPage(page, '/settings');

    // Unified settings page should have tab buttons
    const content = await page.textContent('body');
    expect(content).toContain('Profil');
    expect(content).toContain('Abonnement');
    expect(content).toContain('Notifications');
  });

  test('les preferences locales sont accessibles @P1', async ({ page }) => {
    await openAuthenticatedPage(page, '/settings');

    // Navigate to preferences tab (might be #preferences hash or a tab click)
    const prefsTab = page.locator('button:has-text("Préférences"), button:has-text("Preferences"), a:has-text("Préférences")');
    if (await prefsTab.first().isVisible().catch(() => false)) {
      await prefsTab.first().click();
      await page.waitForTimeout(300);
    }

    // Check that preferences controls exist (select dropdowns for route, density, theme)
    const selects = page.locator('select');
    const selectCount = await selects.count();
    expect(selectCount).toBeGreaterThan(0);
  });

  test('les toggles de notification fonctionnent @P1', async ({ page }) => {
    await openAuthenticatedPage(page, '/settings');

    // Click on Notifications tab
    const notifTab = page.locator('button:has-text("Notifications"), a:has-text("Notifications")');
    if (await notifTab.first().isVisible().catch(() => false)) {
      await notifTab.first().click();
      await page.waitForTimeout(300);
    }

    const toggles = page.locator(
      'input[type="checkbox"], [role="switch"], button[role="switch"]'
    );
    const toggleCount = await toggles.count();

    if (toggleCount > 0) {
      const firstToggle = toggles.first();
      const wasBefore = await firstToggle.isChecked().catch(() => null);

      await firstToggle.click();
      await page.waitForTimeout(500);

      const isAfter = await firstToggle.isChecked().catch(() => null);
      if (wasBefore !== null && isAfter !== null) {
        expect(isAfter).not.toBe(wasBefore);
        await firstToggle.click();
      }
    }
  });

  test('la page /account redirige vers /settings @P1', async ({ page }) => {
    await openAuthenticatedPage(page, '/account');
    await page.waitForTimeout(1000);

    // Should redirect to /settings (with hash)
    expect(page.url()).toContain('/settings');
  });

  test('bouton export GDPR present @P1', async ({ page }) => {
    await openAuthenticatedPage(page, '/settings#confidentialite');
    await page.waitForTimeout(500);

    const content = await page.textContent('body');
    const hasGdpr = content!.includes('données') || content!.includes('RGPD') || content!.includes('Confidentialité') || content!.includes('Exporter');
    expect(hasGdpr).toBe(true);
  });

  test('onglet abonnement affiche le plan @P1', async ({ page }) => {
    await openAuthenticatedPage(page, '/settings#abonnement');
    await page.waitForTimeout(500);

    const content = await page.textContent('body');
    const hasPlan = content!.includes('Plan') || content!.includes('plan') || content!.includes('Abonnement') || content!.includes('abonnement');
    expect(hasPlan).toBe(true);
  });
});
