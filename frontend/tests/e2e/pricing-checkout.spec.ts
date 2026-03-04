import { test, expect } from '@playwright/test';

test('Stripe checkout flow', async ({ page }) => {
  await page.goto('/pricing');
  await page.click('button:has-text("Choisir"):first');

  // Should redirect to Stripe
  await expect(page).toHaveURL(/checkout.stripe.com/);
});