import { expect, test, type Page } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

/**
 * Installs API mocks for an authenticated user with an active subscription.
 */
async function installActiveSubscriptionMocks(page: Page) {
	await page.route('**/api/v1/**', async (route) => {
		const request = route.request();
		const method = request.method();
		const url = new URL(request.url());
		const path = url.pathname;

		if (method === 'OPTIONS') {
			await route.fulfill({ status: 204, headers: CORS_HEADERS });
			return;
		}

		if (method === 'GET' && path === '/api/v1/stripe/subscription') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					plan_key: 'starter',
					plan_name: 'Starter',
					status: 'active',
					mode: 'subscription',
					is_active: true,
					entitlements_version: 1,
					max_scis: 1,
					max_biens: 5,
					current_scis: 1,
					current_biens: 1,
					remaining_scis: 0,
					remaining_biens: 4,
					over_limit: false,
					onboarding_completed: true,
					features: {}
				})
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([
					{
						id: 'sci-1',
						nom: 'SCI Test',
						siren: '111222333',
						regime_fiscal: 'IR',
						statut: 'exploitation',
						associes_count: 1,
						biens_count: 1,
						loyers_count: 0,
						user_role: 'gerant',
						user_part: 100,
						associes: []
					}
				])
			});
			return;
		}

		// Default: empty arrays for list endpoints
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify([])
		});
	});
}

/**
 * Installs API mocks for an authenticated user with an inactive subscription.
 */
async function installInactiveSubscriptionMocks(page: Page) {
	await page.route('**/api/v1/**', async (route) => {
		const request = route.request();
		const method = request.method();
		const url = new URL(request.url());
		const path = url.pathname;

		if (method === 'OPTIONS') {
			await route.fulfill({ status: 204, headers: CORS_HEADERS });
			return;
		}

		if (method === 'GET' && path === '/api/v1/stripe/subscription') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					plan_key: 'free',
					plan_name: 'Free',
					status: 'expired',
					mode: 'subscription',
					is_active: false,
					entitlements_version: 1,
					max_scis: 0,
					max_biens: 0,
					current_scis: 0,
					current_biens: 0,
					remaining_scis: 0,
					remaining_biens: 0,
					over_limit: false,
					onboarding_completed: false,
					features: {}
				})
			});
			return;
		}

		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify([])
		});
	});
}

test.describe('Paywall', () => {
	test('unauthenticated user on /dashboard redirects to /login', async ({ page }) => {
		await page.goto('/dashboard');
		await expect(page).toHaveURL(/\/login/);
	});

	test('unauthenticated user on /scis redirects to /login', async ({ page }) => {
		await page.goto('/scis');
		await expect(page).toHaveURL(/\/login/);
	});

	test('unauthenticated user on /settings redirects to /login', async ({ page }) => {
		await page.goto('/settings');
		await expect(page).toHaveURL(/\/login/);
	});

	test('authenticated user with active subscription can access /dashboard', async ({
		page,
		isMobile
	}) => {
		test.skip(isMobile, 'Desktop navigation test');

		await installActiveSubscriptionMocks(page);
		await seedFakeUserContext(page);

		await page.goto('/dashboard');
		await expect(page).not.toHaveURL(/\/login/);
		await expect(page.getByRole('heading', { level: 1 })).toContainText('Dashboard');
	});

	test('authenticated user with inactive subscription is redirected to /pricing', async ({
		page,
		isMobile
	}) => {
		test.skip(isMobile, 'Desktop navigation test');

		await installInactiveSubscriptionMocks(page);
		await seedFakeUserContext(page);

		await page.goto('/dashboard');
		await expect(page).toHaveURL(/\/pricing/);
	});
});
