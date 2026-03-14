import { test, expect } from '@playwright/test';
import { skipIfNoAuth, injectFakeSession, takeScreenshots, SCREENSHOT_DIR } from './helpers/auth';

test.describe.serial('05 — Fiche bien et onglets (authentifie)', () => {
	skipIfNoAuth();

	let firstSciId: string | null = null;
	let firstBienId: string | null = null;

	test.beforeEach(async ({ page }) => {
		await injectFakeSession(page);
	});

	test('Liste des biens — /scis/{id}/biens', async ({ page }) => {
		// First find a SCI with biens
		await page.goto('/scis');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Extract first SCI ID
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

		test.skip(!firstSciId, 'Aucune SCI trouvee');

		await page.goto(`/scis/${firstSciId}/biens`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page).toHaveURL(new RegExp(`/scis/${firstSciId}/biens`));

		// Look for biens content (grid, list, or empty state)
		const pageContent = await page.textContent('body');
		const hasContent =
			pageContent?.includes('Bien') ||
			pageContent?.includes('bien') ||
			pageContent?.includes('Aucun') ||
			pageContent?.includes('Ajouter');

		expect(hasContent).toBeTruthy();

		// Extract first bien ID for tab tests
		const bienLinks = page.locator('a[href*="/biens/"]');
		const bienLinkCount = await bienLinks.count();
		if (bienLinkCount > 0) {
			const bienHref = await bienLinks.first().getAttribute('href');
			if (bienHref) {
				const match = bienHref.match(/\/biens\/([a-f0-9-]+)/);
				if (match) {
					firstBienId = match[1];
				}
			}
		}

		await takeScreenshots(page, '05-biens-list');
	});

	test('Fiche bien — vue generale', async ({ page }) => {
		test.skip(!firstSciId || !firstBienId, 'Aucun bien trouve');

		await page.goto(`/scis/${firstSciId}/biens/${firstBienId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page).toHaveURL(
			new RegExp(`/scis/${firstSciId}/biens/${firstBienId}`)
		);

		// Verify the page has loaded with some content
		const heading = page.locator('h1, h2').first();
		await expect(heading).toBeVisible();

		await takeScreenshots(page, '05-fiche-bien-overview');
	});

	test('Fiche bien — onglet identite', async ({ page }) => {
		test.skip(!firstSciId || !firstBienId, 'Aucun bien trouve');

		await page.goto(`/scis/${firstSciId}/biens/${firstBienId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Look for tabs and click "Identite" if present
		const identiteTab = page.getByRole('tab', { name: /Identité|Identite/i })
			.or(page.getByText(/Identité|Identite/i).locator('button, [role="tab"]'));

		if (await identiteTab.count() > 0) {
			await identiteTab.first().click();
			await page.waitForTimeout(500);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/05-fiche-bien-identite.png`,
			fullPage: false
		});
	});

	test('Fiche bien — onglet bail', async ({ page }) => {
		test.skip(!firstSciId || !firstBienId, 'Aucun bien trouve');

		await page.goto(`/scis/${firstSciId}/biens/${firstBienId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		const bailTab = page.getByRole('tab', { name: /Bail/i })
			.or(page.locator('[role="tab"]').filter({ hasText: /Bail/i }));

		if (await bailTab.count() > 0) {
			await bailTab.first().click();
			await page.waitForTimeout(500);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/05-fiche-bien-bail.png`,
			fullPage: false
		});
	});

	test('Fiche bien — onglet loyers', async ({ page }) => {
		test.skip(!firstSciId || !firstBienId, 'Aucun bien trouve');

		await page.goto(`/scis/${firstSciId}/biens/${firstBienId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		const loyersTab = page.getByRole('tab', { name: /Loyers/i })
			.or(page.locator('[role="tab"]').filter({ hasText: /Loyers/i }));

		if (await loyersTab.count() > 0) {
			await loyersTab.first().click();
			await page.waitForTimeout(500);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/05-fiche-bien-loyers.png`,
			fullPage: false
		});
	});

	test('Fiche bien — onglet charges', async ({ page }) => {
		test.skip(!firstSciId || !firstBienId, 'Aucun bien trouve');

		await page.goto(`/scis/${firstSciId}/biens/${firstBienId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		const chargesTab = page.getByRole('tab', { name: /Charges/i })
			.or(page.locator('[role="tab"]').filter({ hasText: /Charges/i }));

		if (await chargesTab.count() > 0) {
			await chargesTab.first().click();
			await page.waitForTimeout(500);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/05-fiche-bien-charges.png`,
			fullPage: false
		});
	});

	test('Fiche bien — onglet documents', async ({ page }) => {
		test.skip(!firstSciId || !firstBienId, 'Aucun bien trouve');

		await page.goto(`/scis/${firstSciId}/biens/${firstBienId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		const docsTab = page.getByRole('tab', { name: /Documents/i })
			.or(page.locator('[role="tab"]').filter({ hasText: /Documents/i }));

		if (await docsTab.count() > 0) {
			await docsTab.first().click();
			await page.waitForTimeout(500);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/05-fiche-bien-documents.png`,
			fullPage: false
		});
	});

	test('Fiche bien — onglet rentabilite', async ({ page }) => {
		test.skip(!firstSciId || !firstBienId, 'Aucun bien trouve');

		await page.goto(`/scis/${firstSciId}/biens/${firstBienId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		const rentaTab = page.getByRole('tab', { name: /Rentabilité|Rentabilite/i })
			.or(page.locator('[role="tab"]').filter({ hasText: /Rentabilité/i }));

		if (await rentaTab.count() > 0) {
			await rentaTab.first().click();
			await page.waitForTimeout(500);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/05-fiche-bien-rentabilite.png`,
			fullPage: false
		});
	});

	test('Fiche bien — vue complete (full page)', async ({ page }) => {
		test.skip(!firstSciId || !firstBienId, 'Aucun bien trouve');

		await page.goto(`/scis/${firstSciId}/biens/${firstBienId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/05-fiche-bien-full.png`,
			fullPage: true
		});
	});
});
