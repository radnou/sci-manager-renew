import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('complete registration and login', async ({ page }) => {
    // Register
    await page.goto('/register');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'SecurePass123');
    await page.click('button:has-text("Register")');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('logout', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'SecurePass123');
    await page.click('button:has-text("Se connecter")');

    // Logout
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL('/');
  });
});