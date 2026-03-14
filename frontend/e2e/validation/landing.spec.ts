import { test, expect } from '@playwright/test';

test.describe('Landing page @P0', () => {
  test('le CTA hero navigue vers login ou pricing', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // The landing page should have at least one CTA button
    const ctaButtons = page.locator('a[href="/login"], a[href="/pricing"], a[href="/register"]');
    await expect(ctaButtons.first()).toBeVisible();

    // Click the primary CTA and verify navigation
    const firstCta = ctaButtons.first();
    const href = await firstCta.getAttribute('href');
    await firstCta.click();
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain(href);
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
