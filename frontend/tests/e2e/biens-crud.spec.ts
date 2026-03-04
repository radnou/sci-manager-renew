import { test, expect } from '@playwright/test';

test.describe('Biens CRUD', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'SecurePass123');
    await page.click('button:has-text("Se connecter")');
  });

  test('create bien', async ({ page }) => {
    await page.goto('/biens');
    await page.click('button:has-text("Ajouter bien")');

    await page.fill('input[name="adresse"]', '10 rue Test');
    await page.fill('input[name="ville"]', 'Paris');
    await page.fill('input[name="code_postal"]', '75001');
    await page.fill('input[name="loyer_cc"]', '1500');

    await page.click('button:has-text("Enregistrer")');

    await expect(page.locator('table')).toContainText('10 rue Test');
  });

  test('generate quitus PDF', async ({ page }) => {
    await page.goto('/loyers');
    await page.click('button:has-text("Générer quitus")');

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('button:has-text("Télécharger PDF")')
    ]);

    expect(download.suggestedFilename()).toContain('quitus');
  });
});