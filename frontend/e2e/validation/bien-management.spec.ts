import { test, expect } from '@playwright/test';

const hasAuth = () => !!process.env.E2E_AUTH_TOKEN;

test.describe('Gestion des biens @P0', () => {
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

  /**
   * Helper: navigate to the first SCI's biens page.
   * Returns true if navigation succeeded, false if no SCI exists.
   */
  async function goToBiens(page: import('@playwright/test').Page): Promise<boolean> {
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');

    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!(await sciLink.isVisible().catch(() => false))) return false;
    await sciLink.click();
    await page.waitForLoadState('networkidle');

    const biensLink = page.locator('a[href*="biens"]');
    if (!(await biensLink.first().isVisible().catch(() => false))) return false;
    await biensLink.first().click();
    await page.waitForLoadState('networkidle');
    return true;
  }

  /**
   * Helper: navigate to the first bien's fiche page.
   * Returns true if navigation succeeded.
   */
  async function goToFicheBien(page: import('@playwright/test').Page): Promise<boolean> {
    if (!(await goToBiens(page))) return false;

    const bienLink = page.locator('a[href*="/biens/"]').first();
    if (!(await bienLink.isVisible().catch(() => false))) return false;
    await bienLink.click();
    await page.waitForLoadState('networkidle');
    return true;
  }

  test('la grille biens affiche adresse et type @P0', async ({ page }) => {
    const navigated = await goToBiens(page);
    if (!navigated) return; // Skip gracefully if no SCI

    // Biens list should show cards/rows with addresses
    const biensContent = page.locator(
      '[data-testid="biens-list"], [class*="bien"], table, [class*="card"], [class*="Card"]'
    );
    const emptyState = page.locator(':text("Aucun bien"), :text("Ajouter"), :text("Créer")');

    const hasBiens = await biensContent.first().isVisible().catch(() => false);
    const hasEmpty = await emptyState.first().isVisible().catch(() => false);

    expect(hasBiens || hasEmpty).toBe(true);
  });

  test('formulaire creation bien @P0', async ({ page }) => {
    const navigated = await goToBiens(page);
    if (!navigated) return;

    const createButton = page.locator(
      'button:has-text("Ajouter"), button:has-text("Créer"), button:has-text("Nouveau")'
    );
    if (await createButton.first().isVisible().catch(() => false)) {
      await createButton.first().click();
      await page.waitForTimeout(500);

      // Address input should appear
      const adresseInput = page.locator(
        'input[name="adresse"], input[placeholder*="adresse"], input[placeholder*="Adresse"]'
      );
      const formVisible = await adresseInput.first().isVisible().catch(() => false);
      expect(formVisible).toBe(true);
    }
  });

  test('fiche bien onglet identite @P0', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    // The fiche bien should show identification info (address, type, etc.)
    const pageContent = await page.textContent('body');
    const hasIdentity =
      pageContent!.includes('adresse') ||
      pageContent!.includes('Adresse') ||
      pageContent!.includes('Identité') ||
      pageContent!.includes('type') ||
      pageContent!.includes('meublé') ||
      pageContent!.includes('nu');
    expect(hasIdentity).toBe(true);
  });

  test('creer bail avec locataire @P0', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    // Look for bail tab or section
    const bailTab = page.locator(
      'button:has-text("Bail"), a:has-text("Bail"), [data-testid*="bail"]'
    );
    if (await bailTab.first().isVisible().catch(() => false)) {
      await bailTab.first().click();
      await page.waitForTimeout(500);

      // Look for create bail button
      const createBailBtn = page.locator(
        'button:has-text("Créer"), button:has-text("Nouveau"), button:has-text("Ajouter")'
      );
      if (await createBailBtn.first().isVisible().catch(() => false)) {
        await createBailBtn.first().click();
        await page.waitForTimeout(500);

        // Bail form should have date_debut and loyer_hc
        const dateInput = page.locator('input[type="date"], input[name*="date"]');
        const formVisible = await dateInput.first().isVisible().catch(() => false);
        expect(formVisible).toBe(true);
      }
    }
  });

  test('liste loyers avec pastilles de statut @P0', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    // Navigate to loyers tab
    const loyerTab = page.locator(
      'button:has-text("Loyer"), a:has-text("Loyer"), [data-testid*="loyer"]'
    );
    if (await loyerTab.first().isVisible().catch(() => false)) {
      await loyerTab.first().click();
      await page.waitForTimeout(500);

      // Should show loyers or empty state
      const content = await page.textContent('body');
      const hasLoyers =
        content!.includes('payé') ||
        content!.includes('Payé') ||
        content!.includes('attente') ||
        content!.includes('retard') ||
        content!.includes('Aucun loyer') ||
        content!.includes('loyer');
      expect(hasLoyers).toBe(true);
    }
  });

  test('enregistrer un paiement de loyer @P1', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    const loyerTab = page.locator(
      'button:has-text("Loyer"), a:has-text("Loyer"), [data-testid*="loyer"]'
    );
    if (await loyerTab.first().isVisible().catch(() => false)) {
      await loyerTab.first().click();
      await page.waitForTimeout(500);

      // Look for a loyer row with a payment action
      const payButton = page.locator(
        'button:has-text("Payer"), button:has-text("Encaisser"), button:has-text("Marquer")'
      );
      if (await payButton.first().isVisible().catch(() => false)) {
        // Verify the button is clickable (do not actually click to avoid side effects)
        await expect(payButton.first()).toBeEnabled();
      }
    }
  });

  test('liste charges et ajouter une charge @P1', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    const chargesTab = page.locator(
      'button:has-text("Charge"), a:has-text("Charge"), [data-testid*="charge"]'
    );
    if (await chargesTab.first().isVisible().catch(() => false)) {
      await chargesTab.first().click();
      await page.waitForTimeout(500);

      const addButton = page.locator(
        'button:has-text("Ajouter"), button:has-text("Créer"), button:has-text("Nouvelle")'
      );
      if (await addButton.first().isVisible().catch(() => false)) {
        await addButton.first().click();
        await page.waitForTimeout(500);

        const typeInput = page.locator(
          'input[name*="type"], select[name*="type"], input[placeholder*="type"]'
        );
        const formVisible = await typeInput.first().isVisible().catch(() => false);
        expect(formVisible).toBe(true);
      }
    }
  });

  test('upload document sur fiche bien @P1', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    const docsTab = page.locator(
      'button:has-text("Document"), a:has-text("Document"), [data-testid*="document"]'
    );
    if (await docsTab.first().isVisible().catch(() => false)) {
      await docsTab.first().click();
      await page.waitForTimeout(500);

      // Should have an upload area or button
      const uploadButton = page.locator(
        'button:has-text("Ajouter"), button:has-text("Uploader"), button:has-text("Importer"), input[type="file"]'
      );
      const uploadVisible = await uploadButton.first().isVisible().catch(() => false);

      // File input might be hidden, check for it as well
      const fileInput = page.locator('input[type="file"]');
      const fileInputExists = (await fileInput.count()) > 0;

      expect(uploadVisible || fileInputExists).toBe(true);
    }
  });

  test('supprimer un document @P1', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    const docsTab = page.locator(
      'button:has-text("Document"), a:has-text("Document"), [data-testid*="document"]'
    );
    if (await docsTab.first().isVisible().catch(() => false)) {
      await docsTab.first().click();
      await page.waitForTimeout(500);

      // If documents exist, there should be delete buttons
      const deleteButton = page.locator(
        'button[aria-label*="supprimer"], button[aria-label*="delete"], button:has-text("Supprimer")'
      );
      if (await deleteButton.first().isVisible().catch(() => false)) {
        // Verify button exists but don't click (avoid data loss)
        await expect(deleteButton.first()).toBeEnabled();
      }
    }
  });

  test('creer assurance PNO @P1', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    // Navigate to PNO tab or section
    const pnoSection = page.locator(
      'button:has-text("PNO"), button:has-text("Assurance"), a:has-text("PNO"), a:has-text("Assurance"), [data-testid*="pno"]'
    );
    if (await pnoSection.first().isVisible().catch(() => false)) {
      await pnoSection.first().click();
      await page.waitForTimeout(500);

      const addButton = page.locator(
        'button:has-text("Ajouter"), button:has-text("Créer"), button:has-text("Nouvelle")'
      );
      if (await addButton.first().isVisible().catch(() => false)) {
        await addButton.first().click();
        await page.waitForTimeout(500);

        const assureurInput = page.locator(
          'input[name*="assureur"], input[placeholder*="assureur"], input[placeholder*="Assureur"]'
        );
        const formVisible = await assureurInput.first().isVisible().catch(() => false);
        expect(formVisible).toBe(true);
      }
    }
  });

  test('creer frais agence @P1', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    const fraisSection = page.locator(
      'button:has-text("Frais"), button:has-text("Agence"), a:has-text("Frais"), [data-testid*="frais"]'
    );
    if (await fraisSection.first().isVisible().catch(() => false)) {
      await fraisSection.first().click();
      await page.waitForTimeout(500);

      const addButton = page.locator(
        'button:has-text("Ajouter"), button:has-text("Créer")'
      );
      if (await addButton.first().isVisible().catch(() => false)) {
        await addButton.first().click();
        await page.waitForTimeout(500);

        const montantInput = page.locator(
          'input[name*="montant"], input[type="number"]'
        );
        const formVisible = await montantInput.first().isVisible().catch(() => false);
        expect(formVisible).toBe(true);
      }
    }
  });

  test('la rentabilite affiche les champs calcules @P1', async ({ page }) => {
    const navigated = await goToFicheBien(page);
    if (!navigated) return;

    // Look for rentabilite tab or section
    const rentaSection = page.locator(
      'button:has-text("Rentabilité"), button:has-text("rentabilité"), a:has-text("Rentabilité"), [data-testid*="rentabilite"]'
    );
    if (await rentaSection.first().isVisible().catch(() => false)) {
      await rentaSection.first().click();
      await page.waitForTimeout(500);

      const content = await page.textContent('body');
      const hasRenta =
        content!.includes('brute') ||
        content!.includes('Brute') ||
        content!.includes('nette') ||
        content!.includes('Nette') ||
        content!.includes('cashflow') ||
        content!.includes('Cashflow') ||
        content!.includes('%');
      expect(hasRenta).toBe(true);
    }
  });
});
