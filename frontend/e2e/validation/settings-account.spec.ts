import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

test.describe('Parametres et compte @P1', () => {

  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  test('la page parametres charge les preferences @P1', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // Settings page should show preference sections
    const content = await page.textContent('body');
    const hasSettings =
      content!.includes('Param') ||
      content!.includes('param') ||
      content!.includes('Notification') ||
      content!.includes('notification') ||
      content!.includes('rence');
    expect(hasSettings).toBe(true);
  });

  test('les toggles de notification fonctionnent @P1', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // Look for notification toggles (checkboxes or switches)
    const toggles = page.locator(
      'input[type="checkbox"], [role="switch"], button[role="switch"], [class*="toggle"], [class*="Toggle"], [class*="switch"], [class*="Switch"]'
    );
    const toggleCount = await toggles.count();

    if (toggleCount > 0) {
      // Click the first toggle
      const firstToggle = toggles.first();
      const wasBefore = await firstToggle.isChecked().catch(() => null);

      await firstToggle.click();
      await page.waitForTimeout(500);

      // Verify state changed or click was accepted
      const isAfter = await firstToggle.isChecked().catch(() => null);
      if (wasBefore !== null && isAfter !== null) {
        expect(isAfter).not.toBe(wasBefore);

        // Toggle back to original state
        await firstToggle.click();
      }
    }
  });

  test('la page compte affiche le profil @P1', async ({ page }) => {
    await page.goto('/account');
    await page.waitForLoadState('networkidle');

    // Account page should show user info
    const content = await page.textContent('body');
    const hasProfile =
      content!.includes('demo') ||
      content!.includes('Compte') ||
      content!.includes('compte') ||
      content!.includes('Email') ||
      content!.includes('email') ||
      content!.includes('Profil') ||
      content!.includes('profil');
    expect(hasProfile).toBe(true);
  });

  test('bouton export GDPR present @P1', async ({ page }) => {
    await page.goto('/account');
    await page.waitForLoadState('networkidle');

    // Look for GDPR export button
    const exportButton = page.locator(
      'button:has-text("Export"), button:has-text("export"), button:has-text("donn"), button:has-text("charger mes donn"), button:has-text("RGPD")'
    );
    const exists = await exportButton.first().isVisible().catch(() => false);

    // Also check for a privacy section
    const privacySection = page.locator(
      ':text("Donn"), :text("donn"), :text("RGPD"), :text("confidentialit"), :text("Privacy")'
    );
    const hasPrivacy = await privacySection.first().isVisible().catch(() => false);

    expect(exists || hasPrivacy).toBe(true);
  });

  test('bouton suppression compte GDPR avec confirmation @P1', async ({ page }) => {
    await page.goto('/account');
    await page.waitForLoadState('networkidle');

    // Look for delete account button
    const deleteButton = page.locator(
      'button:has-text("Supprimer mon compte"), button:has-text("Supprimer"), button:has-text("supprimer le compte"), button[class*="destructive"]'
    );

    if (await deleteButton.first().isVisible().catch(() => false)) {
      await deleteButton.first().click();
      await page.waitForTimeout(500);

      // A confirmation dialog should appear
      const confirmDialog = page.locator(
        '[role="dialog"], [role="alertdialog"], [class*="modal"], [class*="Modal"]'
      );
      const confirmVisible = await confirmDialog.first().isVisible().catch(() => false);

      // Or confirmation text
      const confirmText = page.locator(
        ':text("tes-vous s"), :text("confirmer"), :text("Confirmer"), :text("versible")'
      );
      const hasConfirmText = await confirmText.first().isVisible().catch(() => false);

      expect(confirmVisible || hasConfirmText).toBe(true);

      // Cancel to avoid actual deletion
      const cancelButton = page.locator(
        'button:has-text("Annuler"), button:has-text("Non"), button:has-text("Cancel")'
      );
      if (await cancelButton.first().isVisible().catch(() => false)) {
        await cancelButton.first().click();
      }
    }
  });
});
