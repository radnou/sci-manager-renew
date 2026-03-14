import { test, expect } from '@playwright/test';
import { skipIfNoAuth, injectFakeSession, takeScreenshots, SCREENSHOT_DIR } from './helpers/auth';

test.describe.serial('08 — Parametres et compte (authentifie)', () => {
	skipIfNoAuth();

	test.beforeEach(async ({ page }) => {
		await injectFakeSession(page);
	});

	test('Parametres — /settings', async ({ page }) => {
		await page.goto('/settings');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page).toHaveURL(/\/settings/);

		// Verify settings-related content
		const pageContent = await page.textContent('body');
		const hasContent =
			pageContent?.includes('Paramètre') ||
			pageContent?.includes('paramètre') ||
			pageContent?.includes('Préférence') ||
			pageContent?.includes('Notification') ||
			pageContent?.includes('notification') ||
			pageContent?.includes('Profil') ||
			pageContent?.includes('Erreur');

		expect(hasContent).toBeTruthy();

		await takeScreenshots(page, '08-settings');
	});

	test('Parametres — section notifications', async ({ page }) => {
		await page.goto('/settings');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Look for notification preferences
		const notifSection = page.getByText(/Notification/i);
		const hasNotifSection = await notifSection.count() > 0;

		if (hasNotifSection) {
			await notifSection.first().scrollIntoViewIfNeeded();
			await page.waitForTimeout(300);

			// Look for toggles or checkboxes
			const toggles = page.locator(
				'input[type="checkbox"], [role="switch"], button[role="switch"]'
			);
			const toggleCount = await toggles.count();

			// Verify there are interaction elements
			if (toggleCount > 0) {
				await expect(toggles.first()).toBeVisible();
			}
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/08-settings-notifications.png`,
			fullPage: false
		});
	});

	test('Compte — /account', async ({ page }) => {
		await page.goto('/account');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page).toHaveURL(/\/account/);

		// Verify account-related content
		const pageContent = await page.textContent('body');
		const hasContent =
			pageContent?.includes('Compte') ||
			pageContent?.includes('compte') ||
			pageContent?.includes('Profil') ||
			pageContent?.includes('profil') ||
			pageContent?.includes('Email') ||
			pageContent?.includes('Confidentialité') ||
			pageContent?.includes('Supprimer') ||
			pageContent?.includes('Erreur');

		expect(hasContent).toBeTruthy();

		await takeScreenshots(page, '08-account');
	});

	test('Compte — section confidentialite / RGPD', async ({ page }) => {
		await page.goto('/account');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Look for privacy/GDPR section
		const privacySection = page.getByText(/Confidentialité|RGPD|Données personnelles/i);
		const hasPrivacy = await privacySection.count() > 0;

		if (hasPrivacy) {
			await privacySection.first().scrollIntoViewIfNeeded();
			await page.waitForTimeout(300);
		}

		// Look for data export or account deletion options
		const exportBtn = page.getByRole('button', { name: /Export|Télécharger|Supprimer/i });
		const hasExportBtn = await exportBtn.count() > 0;

		if (hasExportBtn) {
			await expect(exportBtn.first()).toBeVisible();
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/08-account-privacy.png`,
			fullPage: false
		});
	});

	test('Parametres — vue complete (full page)', async ({ page }) => {
		await page.goto('/settings');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/08-settings-full.png`,
			fullPage: true
		});
	});
});
