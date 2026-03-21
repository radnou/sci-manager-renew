import { expect } from '@playwright/test';
import { test } from '../fixtures/auth.fixture';

const sciId = process.env.E2E_SCI_ID;
const bienId = process.env.E2E_BIEN_ID;

test.describe('Smoke prod authentifie', () => {
  test.beforeEach(async () => {
    test.skip(!process.env.E2E_AUTH_TOKEN, 'E2E_AUTH_TOKEN manquant');
    test.skip(!sciId, 'E2E_SCI_ID manquant');
    test.skip(!bienId, 'E2E_BIEN_ID manquant');
  });

  test('dashboard et finances chargent sans erreur console', async ({ authedPage: page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    await page.goto('/finances');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Finances' })).toBeVisible();

    expect(consoleErrors).toEqual([]);
  });

  test('documents agreges affichent un etat utile', async ({ authedPage: page }) => {
    await page.goto(`/scis/${sciId}/documents`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'Documents' })).toBeVisible();
    await expect(page.getByText(/Aucun document|Ajouter|Ouvrir/).first()).toBeVisible();
  });

  test('fiche bien: modales exclusives et message quittance coherent', async ({ authedPage: page }) => {
    await page.goto(`/scis/${sciId}/biens/${bienId}`);
    await page.waitForLoadState('networkidle');
    const visibleDialogs = page.locator('[role="dialog"]:visible');

    await page.locator('#section-identite').getByRole('button', { name: 'Modifier' }).click();
    await expect(page.locator('#section-identite')).toBeVisible();

    await page.getByRole('button', { name: 'Enregistrer un loyer' }).click();
    await expect(visibleDialogs).toHaveCount(1);

    await page.getByRole('button', { name: 'Ajouter une charge' }).click();
    await expect(visibleDialogs).toHaveCount(1);

    await page.getByRole('button', { name: 'Générer quittance' }).click();
    await expect(page.getByText(/Aucun bail actif|Aucun locataire associé au bail|Aucun loyer payé/)).toBeVisible();
  });

  test('fiscalite ne doit pas produire d erreur console', async ({ authedPage: page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(`/scis/${sciId}/fiscalite`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'Fiscalité' })).toBeVisible();
    expect(consoleErrors).toEqual([]);
  });
});
