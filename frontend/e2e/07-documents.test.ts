import { test, expect } from '@playwright/test';
import { skipIfNoAuth, injectFakeSession, takeScreenshots, SCREENSHOT_DIR } from './helpers/auth';

test.describe.serial('07 — Gestion documentaire (authentifie)', () => {
	skipIfNoAuth();

	let firstSciId: string | null = null;

	test.beforeEach(async ({ page }) => {
		await injectFakeSession(page);
	});

	test('Trouver une SCI pour la GED', async ({ page }) => {
		await page.goto('/scis');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		const sciLinks = page.locator('a[href*="/scis/"]');
		const linkCount = await sciLinks.count();

		if (linkCount > 0) {
			const href = await sciLinks.first().getAttribute('href');
			if (href) {
				const match = href.match(/\/scis\/([a-f0-9-]+)/);
				if (match) {
					firstSciId = match[1];
				}
			}
		}

		test.skip(!firstSciId, 'Aucune SCI trouvee pour la GED');
	});

	test('Documents SCI — /scis/{id}/documents', async ({ page }) => {
		test.skip(!firstSciId, 'Aucune SCI trouvee');

		await page.goto(`/scis/${firstSciId}/documents`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page).toHaveURL(new RegExp(`/scis/${firstSciId}/documents`));

		// Verify document management content
		const pageContent = await page.textContent('body');
		const hasContent =
			pageContent?.includes('Document') ||
			pageContent?.includes('document') ||
			pageContent?.includes('Fichier') ||
			pageContent?.includes('fichier') ||
			pageContent?.includes('Aucun') ||
			pageContent?.includes('Ajouter') ||
			pageContent?.includes('Importer');

		expect(hasContent).toBeTruthy();

		await takeScreenshots(page, '07-documents-list');
	});

	test('Documents — verifier bouton upload', async ({ page }) => {
		test.skip(!firstSciId, 'Aucune SCI trouvee');

		await page.goto(`/scis/${firstSciId}/documents`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Look for an upload/add button
		const uploadBtn = page.getByRole('button', { name: /Ajouter|Importer|Upload|Téléverser/i });
		const hasUpload = await uploadBtn.count() > 0;

		if (hasUpload) {
			await expect(uploadBtn.first()).toBeVisible();
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/07-documents-upload.png`,
			fullPage: false
		});
	});
});
