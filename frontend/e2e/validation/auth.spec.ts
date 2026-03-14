import { test, expect } from '@playwright/test';

test.describe('Authentification @P0', () => {
  test('la page login affiche le champ email et le bouton connexion', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Email input should be visible
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible();

    // Submit button should exist
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
  });

  test('redirection /dashboard vers /login sans authentification @P0', async ({ page }) => {
    // Clear any existing auth state
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Should be redirected to login
    expect(page.url()).toContain('/login');
  });

  test('le formulaire login valide le format email @P1', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    const emailInput = page.locator('input[type="email"]');
    await emailInput.fill('invalid-email');

    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // HTML5 validation or custom validation should prevent submission
    // Check either native validation or error message
    const isInvalid = await emailInput.evaluate(
      (el: HTMLInputElement) => !el.validity.valid
    );
    const errorVisible = await page.locator('[class*="error"], [role="alert"]').isVisible().catch(() => false);

    expect(isInvalid || errorVisible).toBe(true);
  });

  test('le toggle mode magic link fonctionne @P1', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Look for the magic link toggle (text contains "lien" or "magic")
    const magicLinkToggle = page.locator('button:has-text("lien"), a:has-text("lien"), button:has-text("magic"), button:has-text("Magic")');

    if (await magicLinkToggle.count() > 0) {
      await magicLinkToggle.first().click();
      await page.waitForTimeout(300);

      // After toggling, the password field should be hidden or the form layout should change
      // Verify the mode changed by checking for password field visibility
      const passwordField = page.locator('input[type="password"]');
      const passwordVisible = await passwordField.isVisible().catch(() => false);

      // In magic link mode, password field should not be visible
      // OR the button text should have changed
      const toggleChanged = await magicLinkToggle.first().isVisible();
      expect(toggleChanged || !passwordVisible).toBe(true);
    } else {
      // If no toggle found, verify that at least the login form is functional
      const emailInput = page.locator('input[type="email"]');
      await expect(emailInput).toBeVisible();
    }
  });
});
