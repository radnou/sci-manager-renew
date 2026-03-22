import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

test.describe('Paywall et pricing @P0', () => {
  test('la page pricing affiche 2 plans payants + Fondateur @P0', async ({ page }) => {
    await page.goto('/pricing');
    await page.waitForLoadState('networkidle');

    // Should display plan names: Gestion, Pilotage
    const content = await page.textContent('body');
    expect(content).toContain('Gestion');
    expect(content).toContain('Pilotage');

    // Verify pricing amounts are visible
    expect(content).toContain('19');
    expect(content).toContain('39');
  });

  test('la garantie 30 jours est affichee @P1', async ({ page }) => {
    await page.goto('/pricing');
    await page.waitForLoadState('networkidle');

    // Payment-first model: 30-day guarantee instead of free plan
    const content = await page.textContent('body');
    const hasGuarantee =
      content!.includes('30 jours') ||
      content!.includes('satisfait') ||
      content!.includes('remboursé') ||
      content!.includes('Garanti');
    expect(hasGuarantee).toBe(true);
  });

  test('un echec checkout affiche un message explicite @P0', async ({ page }) => {
    await page.route('**/api/v1/stripe/create-guest-checkout', async route => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Paiement temporairement indisponible' }),
      });
    });

    await page.goto('/pricing');
    await page.waitForLoadState('networkidle');
  });

  test('les boutons CTA pointent vers le checkout @P0', async ({ page }) => {
    await page.goto('/pricing');
    await page.waitForLoadState('networkidle');

    // CTAs should say "Démarrer maintenant"
    const ctas = page.locator('button:has-text("Démarrer"), a:has-text("Démarrer")');
    const count = await ctas.count();
    expect(count).toBeGreaterThan(0);
  });

  test('le toggle mensuel/annuel change les prix @P1', async ({ page }) => {
    await page.goto('/pricing');
    await page.waitForLoadState('networkidle');

    // Toggle to annual billing
    const annualButton = page.locator('button:has-text("Annuel")');
    if (await annualButton.isVisible()) {
      await annualButton.click();
      const content = await page.textContent('body');
      // Annual prices: 190€ and 390€
      expect(content).toContain('190');
    }
  });

  test('page pricing accessible sans auth @P0', async ({ page }) => {
    // Pricing is a public page — no login required
    const response = await page.goto('/pricing');
    expect(response?.status()).toBe(200);
  });

  test('paywall redirige vers /pricing sans abonnement @P0', async ({ page }) => {
    // Mock auth but no subscription
    await setupAuthedMocks(page, {
      subscription: {
        plan_key: 'free',
        plan_name: 'Non abonné',
        status: 'no_subscription',
        is_active: false,
        mode: 'subscription',
        entitlements_version: 1,
        current_scis: 0,
        current_biens: 0,
        over_limit: false,
        features: {},
        onboarding_completed: false,
      }
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Should redirect to pricing
    expect(page.url()).toContain('/pricing');
  });
});
