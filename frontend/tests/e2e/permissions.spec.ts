import { expect, test, type Page } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

/**
 * Builds API mocks for a user with a specific role (gerant or associe) in a SCI.
 */
async function installPermissionsMocks(page: Page, userRole: 'gerant' | 'associe') {
	const scis = [
		{
			id: 'sci-1',
			nom: 'SCI Permissions Test',
			siren: '333444555',
			regime_fiscal: 'IR',
			statut: 'exploitation',
			associes_count: 2,
			biens_count: 1,
			loyers_count: 1,
			user_role: userRole,
			user_part: userRole === 'gerant' ? 60 : 40,
			associes: [
				{
					id: 'associe-1',
					nom: 'Gérant',
					email: 'gerant@sci.test',
					part: 60,
					role: 'gerant'
				},
				{
					id: 'associe-2',
					nom: 'Associé',
					email: 'associe@sci.test',
					part: 40,
					role: 'associe'
				}
			]
		}
	];

	const biens = [
		{
			id: 'bien-1',
			id_sci: 'sci-1',
			adresse: '1 rue Permissions',
			ville: 'Paris',
			code_postal: '75001',
			type_locatif: 'nu',
			loyer_cc: 1000,
			charges: 100,
			tmi: 30
		}
	];

	const subscription = {
		plan_key: 'pro',
		plan_name: 'Pro',
		status: 'active',
		mode: 'subscription',
		is_active: true,
		entitlements_version: 1,
		max_scis: 10,
		max_biens: 20,
		current_scis: 1,
		current_biens: 1,
		remaining_scis: 9,
		remaining_biens: 19,
		over_limit: false,
		onboarding_completed: true,
		features: {
			multi_sci_enabled: true,
			charges_enabled: true,
			fiscalite_enabled: true,
			quitus_enabled: true,
			cerfa_enabled: true,
			priority_support: true
		}
	};

	const sciDetail = {
		...scis[0],
		charges_count: 0,
		total_monthly_rent: 1000,
		total_monthly_property_charges: 100,
		total_recorded_charges: 0,
		paid_loyers_total: 1000,
		pending_loyers_total: 0,
		biens,
		recent_loyers: [
			{
				id: 'loyer-1',
				id_bien: 'bien-1',
				id_sci: 'sci-1',
				id_locataire: null,
				date_loyer: '2026-03-01',
				montant: 1000,
				statut: 'paye',
				quitus_genere: false
			}
		],
		recent_charges: [],
		fiscalite: []
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
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(sciDetail)
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

		if (method === 'GET' && (path === '/api/v1/associes' || path === '/api/v1/associes/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([
					{
						id: 'associe-1',
						id_sci: 'sci-1',
						user_id: userRole === 'gerant' ? 'user-e2e-001' : null,
						nom: 'Gérant',
						email: 'gerant@sci.test',
						part: 60,
						role: 'gerant',
						is_account_member: userRole === 'gerant'
					},
					{
						id: 'associe-2',
						id_sci: 'sci-1',
						user_id: userRole === 'associe' ? 'user-e2e-001' : null,
						nom: 'Associé',
						email: 'associe@sci.test',
						part: 40,
						role: 'associe',
						is_account_member: userRole === 'associe'
					}
				])
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

test.describe('Permissions — gérant role', () => {
	test.beforeEach(async ({ page, isMobile }) => {
		test.skip(isMobile, 'Desktop navigation test');
		await installPermissionsMocks(page, 'gerant');
		await seedFakeUserContext(page, { email: 'gerant@sci.test', sciId: 'sci-1' });
	});

	test('gérant sees edit/delete buttons on biens page', async ({ page }) => {
		await page.goto('/biens');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

		// Gérant should see modification controls
		await expect(page.getByRole('button', { name: /Modifier/i }).first()).toBeVisible();
		await expect(page.getByRole('button', { name: /Supprimer/i }).first()).toBeVisible();
	});

	test('gérant sees creation button on scis page', async ({ page }) => {
		await page.goto('/scis');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
		await expect(page.getByRole('button', { name: /Créer une SCI/i })).toBeVisible();
	});
});

test.describe('Permissions — associe role', () => {
	test.beforeEach(async ({ page, isMobile }) => {
		test.skip(isMobile, 'Desktop navigation test');
		await installPermissionsMocks(page, 'associe');
		await seedFakeUserContext(page, { email: 'associe@sci.test', sciId: 'sci-1' });
	});

	test('associe can view dashboard without errors', async ({ page }) => {
		await page.goto('/dashboard');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('Dashboard');
	});

	test('associe can view SCI detail page', async ({ page }) => {
		await page.goto('/scis/sci-1');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('SCI Permissions Test');
	});

	test('associe can view biens page', async ({ page }) => {
		await page.goto('/biens');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
	});
});
