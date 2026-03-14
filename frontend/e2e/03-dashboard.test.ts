import { test, expect } from '@playwright/test';
import { skipIfNoAuth, injectFakeSession, takeScreenshots, SCREENSHOT_DIR } from './helpers/auth';

test.describe.serial('03 — Tableau de bord (authentifie)', () => {
	skipIfNoAuth();

	test.beforeEach(async ({ page }) => {
		await injectFakeSession(page);
	});

	test('Dashboard — chargement et titre', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');

		// Verify page loads (not redirected to login)
		await expect(page).toHaveURL(/\/dashboard/);

		// Verify page title
		await expect(page).toHaveTitle(/Cockpit|Dashboard/i);

		// Verify main heading
		await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

		// Verify eyebrow
		await expect(page.getByText('Gestion SCI')).toBeVisible();

		await takeScreenshots(page, '03-dashboard-loaded');
	});

	test('Dashboard — section KPIs', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');

		// Wait for loading to complete (either data or empty state)
		await page.waitForTimeout(2000);

		// The dashboard should show either KPIs or an empty/new-user state
		const hasKpis = await page.locator('[class*="kpi"], [data-testid*="kpi"]').count() > 0;
		const hasEmptyState = await page.getByText(/Bienvenue|Commencer|Aucune SCI/i).count() > 0;
		const hasError = await page.getByText(/Impossible|Erreur|Réessayer/i).count() > 0;

		// At least one of these states should be visible
		expect(hasKpis || hasEmptyState || hasError).toBeTruthy();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/03-dashboard-kpis.png`,
			fullPage: false
		});
	});

	test('Dashboard — section alertes', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Scroll down to find alerts section if it exists
		const alertSection = page.locator('[class*="alert"], [data-testid*="alert"]');
		const alertCount = await alertSection.count();

		if (alertCount > 0) {
			await alertSection.first().scrollIntoViewIfNeeded();
			await page.waitForTimeout(300);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/03-dashboard-alerts.png`,
			fullPage: false
		});
	});

	test('Dashboard — section activite recente', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Look for activity section
		const activitySection = page.getByText(/Activité récente|Dernières actions/i);
		const hasActivity = await activitySection.count() > 0;

		if (hasActivity) {
			await activitySection.first().scrollIntoViewIfNeeded();
			await page.waitForTimeout(300);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/03-dashboard-activity.png`,
			fullPage: false
		});
	});

	test('Dashboard — cartes SCI', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Look for SCI cards section
		const sciCards = page.getByText(/Vos SCI|SCI/i);
		const hasSciCards = await sciCards.count() > 0;

		if (hasSciCards) {
			await sciCards.first().scrollIntoViewIfNeeded();
			await page.waitForTimeout(300);
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/03-dashboard-sci-cards.png`,
			fullPage: false
		});
	});

	test('Dashboard — vue complete (full page)', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/03-dashboard-full.png`,
			fullPage: true
		});
	});
});
