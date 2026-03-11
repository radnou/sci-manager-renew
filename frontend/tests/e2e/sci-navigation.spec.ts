import { expect, test, type Page } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

/**
 * Installs minimal API mocks for navigation smoke tests.
 * All list endpoints return empty arrays; subscription returns active starter.
 */
async function installNavigationMocks(page: Page) {
	const scis = [
		{
			id: 'sci-1',
			nom: 'SCI Navigation Test',
			siren: '999888777',
			regime_fiscal: 'IR',
			statut: 'exploitation',
			associes_count: 1,
			biens_count: 0,
			loyers_count: 0,
			user_role: 'gerant',
			user_part: 100,
			associes: [
				{
					id: 'associe-1',
					nom: 'Test User',
					email: 'nav@sci.test',
					part: 100,
					role: 'gerant'
				}
			]
		}
	];

	const subscription = {
		plan_key: 'starter',
		plan_name: 'Starter',
		status: 'active',
		mode: 'subscription',
		is_active: true,
		entitlements_version: 1,
		max_scis: 1,
		max_biens: 5,
		current_scis: 1,
		current_biens: 0,
		remaining_scis: 0,
		remaining_biens: 5,
		over_limit: false,
		onboarding_completed: true,
		features: {}
	};

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
				body: JSON.stringify(subscription)
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(scis)
			});
			return;
		}

		if (method === 'GET' && path.startsWith('/api/v1/scis/')) {
			const sciId = path.replace(/\/+$/, '').split('/').pop() || '';
			const sci = scis.find((s) => s.id === sciId);
			await route.fulfill({
				status: sci ? 200 : 404,
				contentType: 'application/json',
				body: JSON.stringify(
					sci
						? {
								...sci,
								charges_count: 0,
								total_monthly_rent: 0,
								total_monthly_property_charges: 0,
								total_recorded_charges: 0,
								paid_loyers_total: 0,
								pending_loyers_total: 0,
								biens: [],
								recent_loyers: [],
								recent_charges: [],
								fiscalite: []
							}
						: { detail: 'Not found' }
				)
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

test.describe('SCI Navigation', () => {
	test.beforeEach(async ({ page, isMobile }) => {
		test.skip(isMobile, 'Desktop navigation test');
		await installNavigationMocks(page);
		await seedFakeUserContext(page, { email: 'nav@sci.test' });
	});

	test('dashboard page loads with heading', async ({ page }) => {
		await page.goto('/dashboard');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('Dashboard');
	});

	test('scis page loads with heading', async ({ page }) => {
		await page.goto('/scis');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
	});

	test('finances page loads with heading', async ({ page }) => {
		await page.goto('/finances');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
	});

	test('settings page loads with heading', async ({ page }) => {
		await page.goto('/settings');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
	});

	test('sidebar navigation links are visible', async ({ page }) => {
		await page.goto('/dashboard');
		const sidebar = page.locator('aside').first();
		await expect(sidebar.getByRole('link', { name: 'Dashboard' })).toBeVisible();
		await expect(sidebar.getByRole('link', { name: 'Biens' })).toBeVisible();
		await expect(sidebar.getByRole('link', { name: 'Loyers' })).toBeVisible();
	});

	test('fiche SCI page loads when navigating to /scis/:id', async ({ page }) => {
		await page.goto('/scis/sci-1');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('SCI Navigation Test');
	});
});
