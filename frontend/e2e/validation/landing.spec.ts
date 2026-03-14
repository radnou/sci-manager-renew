import { test, expect } from '@playwright/test';

test.describe('Landing page @P0', () => {
  test('le CTA hero navigue vers login ou pricing', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // The landing/pricing page should have navigation links (Connexion, Inscription)
    const navLinks = page.locator('a:has-text("Connexion"), a:has-text("Inscription")');
    await expect(navLinks.first()).toBeVisible();

    // Verify CTA buttons link to appropriate pages
    const cta = page.locator('a:has-text("Démarrer"), a:has-text("Essayer"), a:has-text("Connexion"), a:has-text("Inscription")');
    const ctaCount = await cta.count();
    expect(ctaCount).toBeGreaterThan(0);

    // Verify at least one CTA has href to login, pricing, or register
    const hrefs: string[] = [];
    for (let i = 0; i < ctaCount; i++) {
      const href = await cta.nth(i).getAttribute('href');
      if (href) hrefs.push(href);
    }
    const hasValidCta = hrefs.some(h => h.includes('login') || h.includes('pricing') || h.includes('register'));
    expect(hasValidCta).toBe(true);
  });

  test('les sections fonctionnalites sont visibles au scroll @P1', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // The landing page should have feature sections with cards or descriptions
    // Scroll to bottom to trigger lazy-loaded content
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Verify feature-related content exists (plans, features, FAQ, etc.)
    const featureCards = page.locator('[class*="card"], [class*="Card"], section');
    const count = await featureCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('responsive: pas de debordement horizontal a 375px @P1', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    expect(hasHorizontalOverflow).toBe(false);
  });
});
