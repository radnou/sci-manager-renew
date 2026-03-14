import { test, expect } from '@playwright/test';
import { hasAuthToken, injectFakeSession, SCREENSHOT_DIR } from './helpers/auth';

/**
 * These tests run exclusively on the mobile-safari project (iPhone 14 viewport).
 * For the desktop-chrome project they will be skipped to avoid duplication.
 *
 * To run only responsive tests:
 *   pnpm exec playwright test --project=mobile-safari 09-responsive
 */

test.describe.serial('09 — Tests responsives (mobile)', () => {
	// Only run in mobile project
	test.skip(({ browserName }) => browserName !== 'webkit', 'Mobile tests: webkit only');

	test('Landing page — mobile viewport', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Verify hero is visible and readable
		const h1 = page.locator('h1');
		await expect(h1).toBeVisible();

		// CTA buttons should stack vertically on mobile
		const ctaSection = page.locator('.flex-col.sm\\:flex-row').first();
		if (await ctaSection.count() > 0) {
			await expect(ctaSection).toBeVisible();
		}

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-landing-hero.png`,
			fullPage: false
		});
	});

	test('Landing page — scroll complet mobile', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-landing-full.png`,
			fullPage: true
		});
	});

	test('Pricing page — mobile viewport', async ({ page }) => {
		await page.goto('/pricing');
		await page.waitForLoadState('networkidle');

		// Plans should stack vertically on mobile
		await expect(page.getByText('Essentiel')).toBeVisible();
		await expect(page.getByText('Gestion')).toBeVisible();
		await expect(page.getByText('Fiscal')).toBeVisible();

		// Billing toggle should be accessible
		await expect(page.getByRole('button', { name: 'Mensuel' })).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-pricing.png`,
			fullPage: false
		});

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-pricing-full.png`,
			fullPage: true
		});
	});

	test('Login page — mobile viewport', async ({ page }) => {
		await page.goto('/login');
		await page.waitForLoadState('networkidle');

		// Form should be usable on mobile
		await expect(page.getByPlaceholder('vous@sci.fr')).toBeVisible();
		await expect(page.getByPlaceholder('••••••••')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Se connecter' })).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-login.png`,
			fullPage: false
		});
	});

	test('Landing page — FAQ accordeon mobile', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		const faqHeading = page.getByText('Tout ce que vous devez savoir');
		await faqHeading.scrollIntoViewIfNeeded();
		await page.waitForTimeout(300);

		// Open a FAQ item
		const firstQuestion = page.getByText('Le produit est-il adapté à une petite SCI familiale ?');
		await firstQuestion.click();
		await page.waitForTimeout(300);

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-faq-open.png`,
			fullPage: false
		});
	});

	test('Landing page — section donnees marche mobile', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		const marketSection = page.getByText('Chiffres clés de la gestion immobilière');
		await marketSection.scrollIntoViewIfNeeded();
		await page.waitForTimeout(300);

		// KPI cards should stack on mobile
		await expect(page.getByText('3,50%')).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-market-data.png`,
			fullPage: false
		});
	});
});

test.describe.serial('09b — Dashboard responsive (mobile + auth)', () => {
	test.skip(({ browserName }) => browserName !== 'webkit', 'Mobile tests: webkit only');
	test.skip(!hasAuthToken(), 'Skipped: E2E_AUTH_TOKEN not set');

	test.beforeEach(async ({ page }) => {
		await injectFakeSession(page);
	});

	test('Dashboard — mobile viewport', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page).toHaveURL(/\/dashboard/);

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-dashboard.png`,
			fullPage: false
		});

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-dashboard-full.png`,
			fullPage: true
		});
	});

	test('Sidebar / navigation — mobile', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1000);

		// Look for a hamburger/menu button (common mobile pattern)
		const menuBtn = page.getByRole('button', { name: /menu|Menu|ouvrir/i })
			.or(page.locator('button[aria-label*="menu" i]'))
			.or(page.locator('[data-testid="mobile-menu"]'));

		const hasMenu = await menuBtn.count() > 0;

		if (hasMenu) {
			await menuBtn.first().click();
			await page.waitForTimeout(500);

			await page.screenshot({
				path: `${SCREENSHOT_DIR}/09-mobile-sidebar-open.png`,
				fullPage: false
			});
		} else {
			// Navigation might always be visible or use a different pattern
			await page.screenshot({
				path: `${SCREENSHOT_DIR}/09-mobile-nav.png`,
				fullPage: false
			});
		}
	});

	test('Finances — mobile viewport', async ({ page }) => {
		await page.goto('/finances');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-finances.png`,
			fullPage: false
		});
	});

	test('Settings — mobile viewport', async ({ page }) => {
		await page.goto('/settings');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/09-mobile-settings.png`,
			fullPage: false
		});
	});
});
