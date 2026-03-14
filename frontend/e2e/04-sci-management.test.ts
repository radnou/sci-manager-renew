import { test, expect } from '@playwright/test';
import { skipIfNoAuth, injectFakeSession, takeScreenshots, SCREENSHOT_DIR } from './helpers/auth';

test.describe.serial('04 — Gestion des SCI (authentifie)', () => {
	skipIfNoAuth();

	let firstSciId: string | null = null;

	test.beforeEach(async ({ page }) => {
		await injectFakeSession(page);
	});

	test('Liste des SCI — /scis', async ({ page }) => {
		await page.goto('/scis');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Verify we're on the SCIs page
		await expect(page).toHaveURL(/\/scis/);

		// Look for SCI-related content (list, cards, or empty state)
		const pageContent = await page.textContent('body');
		const hasSciContent =
			pageContent?.includes('SCI') ||
			pageContent?.includes('Aucune') ||
			pageContent?.includes('Créer');

		expect(hasSciContent).toBeTruthy();

		// Try to capture the first SCI link for subsequent tests
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

		await takeScreenshots(page, '04-scis-list');
	});

	test('Detail SCI — vue principale', async ({ page }) => {
		test.skip(!firstSciId, 'Aucune SCI trouvee pour naviguer');

		await page.goto(`/scis/${firstSciId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Verify we're on the SCI detail page
		await expect(page).toHaveURL(new RegExp(`/scis/${firstSciId}`));

		// Look for SCI overview elements: name, links, calendar
		const heading = page.locator('h1, h2').first();
		await expect(heading).toBeVisible();

		await takeScreenshots(page, '04-sci-detail');
	});

	test('Associes — /scis/{id}/associes', async ({ page }) => {
		test.skip(!firstSciId, 'Aucune SCI trouvee pour naviguer');

		await page.goto(`/scis/${firstSciId}/associes`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page).toHaveURL(new RegExp(`/scis/${firstSciId}/associes`));

		// Look for associates-related content
		const pageContent = await page.textContent('body');
		const hasContent =
			pageContent?.includes('Associé') ||
			pageContent?.includes('associé') ||
			pageContent?.includes('Parts') ||
			pageContent?.includes('Aucun') ||
			pageContent?.includes('Ajouter');

		expect(hasContent).toBeTruthy();

		await takeScreenshots(page, '04-sci-associes');
	});

	test('Fiscalite — /scis/{id}/fiscalite', async ({ page }) => {
		test.skip(!firstSciId, 'Aucune SCI trouvee pour naviguer');

		await page.goto(`/scis/${firstSciId}/fiscalite`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page).toHaveURL(new RegExp(`/scis/${firstSciId}/fiscalite`));

		// Look for fiscal-related content
		const pageContent = await page.textContent('body');
		const hasContent =
			pageContent?.includes('Fiscal') ||
			pageContent?.includes('fiscal') ||
			pageContent?.includes('Régime') ||
			pageContent?.includes('Revenus') ||
			pageContent?.includes('Charges') ||
			pageContent?.includes('Aucun');

		expect(hasContent).toBeTruthy();

		await takeScreenshots(page, '04-sci-fiscalite');
	});

	test('Navigation sidebar — liens SCI visibles', async ({ page }) => {
		test.skip(!firstSciId, 'Aucune SCI trouvee pour naviguer');

		await page.goto(`/scis/${firstSciId}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1000);

		// Check sidebar or navigation for SCI sub-pages
		const nav = page.locator('nav, [role="navigation"], aside');
		const navCount = await nav.count();

		if (navCount > 0) {
			// Look for navigation links to SCI sub-pages
			const bienLink = page.locator('a[href*="biens"]');
			const associesLink = page.locator('a[href*="associes"]');
			const fiscaliteLink = page.locator('a[href*="fiscalite"]');

			if (await bienLink.count() > 0) {
				await expect(bienLink.first()).toBeVisible();
			}
			if (await associesLink.count() > 0) {
				await expect(associesLink.first()).toBeVisible();
			}
			if (await fiscaliteLink.count() > 0) {
				await expect(fiscaliteLink.first()).toBeVisible();
			}
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/04-sci-navigation.png`,
			fullPage: false
		});
	});
});
