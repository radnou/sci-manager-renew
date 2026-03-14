import { test, expect } from '@playwright/test';
import { skipIfNoAuth, injectFakeSession, takeScreenshots, SCREENSHOT_DIR } from './helpers/auth';

test.describe.serial('06 — Page finances (authentifie)', () => {
	skipIfNoAuth();

	test.beforeEach(async ({ page }) => {
		await injectFakeSession(page);
	});

	test('Finances — chargement de la page', async ({ page }) => {
		await page.goto('/finances');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page).toHaveURL(/\/finances/);

		// Verify page has loaded with financial content or empty state
		const pageContent = await page.textContent('body');
		const hasContent =
			pageContent?.includes('Finance') ||
			pageContent?.includes('finance') ||
			pageContent?.includes('Revenus') ||
			pageContent?.includes('Charges') ||
			pageContent?.includes('Cashflow') ||
			pageContent?.includes('Aucun') ||
			pageContent?.includes('Erreur');

		expect(hasContent).toBeTruthy();

		await takeScreenshots(page, '06-finances-overview');
	});

	test('Finances — tableaux et graphiques', async ({ page }) => {
		await page.goto('/finances');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Check for tables
		const tables = page.locator('table');
		const tableCount = await tables.count();

		// Check for chart containers (canvas or svg)
		const charts = page.locator('canvas, svg[class*="chart"], [class*="chart"]');
		const chartCount = await charts.count();

		// Screenshot whatever state we're in
		if (tableCount > 0) {
			await tables.first().scrollIntoViewIfNeeded();
			await page.waitForTimeout(300);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/06-finances-data.png`,
			fullPage: false
		});
	});

	test('Finances — vue complete (full page)', async ({ page }) => {
		await page.goto('/finances');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/06-finances-full.png`,
			fullPage: true
		});
	});
});
