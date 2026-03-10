import { expect, test, type Page } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

/**
 * Installs API mocks simulating a FREE-tier user at capacity:
 * - 1 SCI (max 1), 1 bien (max 1)
 * - remaining_scis=0, remaining_biens=0, over_limit=false
 * The UI should display quota-reached messages and disable creation buttons.
 */
async function installFreeTierAtCapacityMocks(page: Page) {
	const scis = [
		{
			id: 'sci-1',
			nom: 'SCI Unique',
			siren: '111111111',
			regime_fiscal: 'IR',
			statut: 'exploitation',
			associes_count: 1,
			biens_count: 1,
			loyers_count: 0,
			user_role: 'gerant',
			user_part: 100,
			associes: [
				{
					id: 'associe-1',
					nom: 'Free User',
					email: 'free@sci.test',
					part: 100,
					role: 'gerant'
				}
			]
		}
	];

	const biens = [
		{
			id: 'bien-1',
			id_sci: 'sci-1',
			adresse: '1 rue Free',
			ville: 'Paris',
			code_postal: '75001',
			type_locatif: 'nu',
			loyer_cc: 800,
			charges: 50,
			tmi: 30
		}
	];

	const subscription = {
		plan_key: 'free',
		plan_name: 'Free',
		status: 'active',
		mode: 'subscription',
		is_active: true,
		entitlements_version: 1,
		max_scis: 1,
		max_biens: 1,
		current_scis: 1,
		current_biens: 1,
		remaining_scis: 0,
		remaining_biens: 0,
		over_limit: false,
		features: {
			multi_sci_enabled: false,
			charges_enabled: false,
			fiscalite_enabled: false,
			quitus_enabled: true,
			cerfa_enabled: false,
			priority_support: false
		}
	};

	await page.route('**/api/v1/**', async (route) => {
		const request = route.request();
		const method = request.method();
		const url = new URL(request.url());
		const path = url.pathname;

		if (method === 'OPTIONS') {
			await route.fulfill({
				status: 204,
				headers: {
					'access-control-allow-origin': '*',
					'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
					'access-control-allow-headers': '*'
				}
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

		if (method === 'GET' && path === '/api/v1/stripe/subscription') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(subscription)
			});
			return;
		}

		if (method === 'GET' && path.startsWith('/api/v1/scis/')) {
			const sciId = path.replace(/\/+$/, '').split('/').pop() || '';
			const sci = scis.find((s) => s.id === sciId);
			if (!sci) {
				await route.fulfill({ status: 404, contentType: 'application/json', body: '{}' });
				return;
			}
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					...sci,
					charges_count: 0,
					total_monthly_rent: 800,
					total_monthly_property_charges: 50,
					total_recorded_charges: 0,
					paid_loyers_total: 0,
					pending_loyers_total: 0,
					biens,
					recent_loyers: [],
					recent_charges: [],
					fiscalite: []
				})
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/biens' || path === '/api/v1/biens/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(biens)
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/locataires' || path === '/api/v1/locataires/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([])
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/loyers' || path === '/api/v1/loyers/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([])
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/charges' || path === '/api/v1/charges/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([])
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/fiscalite' || path === '/api/v1/fiscalite/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([])
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/associes' || path === '/api/v1/associes/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([
					{
						id: 'associe-1',
						id_sci: 'sci-1',
						user_id: 'user-e2e-001',
						nom: 'Free User',
						email: 'free@sci.test',
						part: 100,
						role: 'gerant',
						is_account_member: true
					}
				])
			});
			return;
		}

		// POST attempts to create beyond quota → 402
		if (method === 'POST' && (path === '/api/v1/biens' || path === '/api/v1/biens/')) {
			await route.fulfill({
				status: 402,
				contentType: 'application/json',
				body: JSON.stringify({
					error: 'Le quota biens est atteint.',
					code: 'plan_limit_reached',
					details: { resource: 'biens' }
				})
			});
			return;
		}

		if (method === 'POST' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			await route.fulfill({
				status: 402,
				contentType: 'application/json',
				body: JSON.stringify({
					error: 'Le quota SCI est atteint.',
					code: 'plan_limit_reached',
					details: { resource: 'scis' }
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

test.describe('Plan limit enforcement UI', () => {
	test('free-tier user at SCI capacity sees disabled creation button on /scis', async ({
		page,
		isMobile
	}) => {
		test.skip(isMobile, 'Desktop navigation test');

		await installFreeTierAtCapacityMocks(page);
		await seedFakeUserContext(page, { email: 'free@sci.test' });

		await page.goto('/scis');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

		// The "Créer une SCI" button should be disabled when quota is reached
		const createButton = page.getByRole('button', { name: 'Créer une SCI' });
		await expect(createButton).toBeVisible();
		await expect(createButton).toBeDisabled();

		// Quota message should be visible
		await expect(
			page.getByText("Le quota de SCI de l'offre active est atteint")
		).toBeVisible();
	});

	test('free-tier user at biens capacity sees quota message on /biens', async ({
		page,
		isMobile
	}) => {
		test.skip(isMobile, 'Desktop navigation test');

		await installFreeTierAtCapacityMocks(page);
		await seedFakeUserContext(page, { email: 'free@sci.test' });

		await page.goto('/biens');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

		// The short quota message in the patrimoine card is visible
		await expect(page.getByText("Le quota de l'offre est atteint.")).toBeVisible();
	});

	test('free-tier user sees plan name and quota on settings page', async ({ page, isMobile }) => {
		test.skip(isMobile, 'Desktop navigation test');

		await installFreeTierAtCapacityMocks(page);
		await seedFakeUserContext(page, { email: 'free@sci.test' });

		await page.goto('/settings');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

		// Scroll to bottom to make the capacity card visible
		await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

		// The plan name "Free" should be visible in a capacity card
		await expect(page.getByText('Free').first()).toBeVisible({ timeout: 5000 });

		// Quota text includes remaining counts
		await expect(page.getByText('0 SCI restantes').first()).toBeVisible({ timeout: 5000 });
	});
});
