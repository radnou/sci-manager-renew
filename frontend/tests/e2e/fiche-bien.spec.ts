import { expect, test, type Page } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

/**
 * Installs API mocks with a fully populated SCI detail for fiche bien tests.
 */
async function installFicheBienMocks(page: Page) {
	const sci = {
		id: 'sci-1',
		nom: 'SCI Fiche Test',
		siren: '555666777',
		regime_fiscal: 'IR',
		statut: 'exploitation',
		associes_count: 2,
		biens_count: 2,
		loyers_count: 1,
		user_role: 'gerant',
		user_part: 60,
		associes: [
			{
				id: 'associe-1',
				nom: 'Gérant Principal',
				email: 'gerant@sci.test',
				part: 60,
				role: 'gerant'
			},
			{
				id: 'associe-2',
				nom: 'Associé Passif',
				email: 'passif@sci.test',
				part: 40,
				role: 'associe'
			}
		]
	};

	const biens = [
		{
			id: 'bien-1',
			id_sci: 'sci-1',
			adresse: '10 rue de la Paix',
			ville: 'Paris',
			code_postal: '75002',
			type_locatif: 'nu',
			loyer_cc: 1500,
			charges: 200,
			tmi: 30
		},
		{
			id: 'bien-2',
			id_sci: 'sci-1',
			adresse: '5 avenue Victor Hugo',
			ville: 'Lyon',
			code_postal: '69003',
			type_locatif: 'meuble',
			loyer_cc: 900,
			charges: 100,
			tmi: 20
		}
	];

	const loyers = [
		{
			id: 'loyer-1',
			id_bien: 'bien-1',
			id_sci: 'sci-1',
			id_locataire: 'loc-1',
			date_loyer: '2026-03-01',
			montant: 1500,
			statut: 'paye',
			quitus_genere: true
		}
	];

	const locataires = [
		{
			id: 'loc-1',
			id_bien: 'bien-1',
			id_sci: 'sci-1',
			nom: 'Marie Durand',
			email: 'marie@locataire.test',
			date_debut: '2025-06-01',
			date_fin: null
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
		current_biens: 2,
		remaining_scis: 9,
		remaining_biens: 18,
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
		...sci,
		charges_count: 0,
		total_monthly_rent: 2400,
		total_monthly_property_charges: 300,
		total_recorded_charges: 0,
		paid_loyers_total: 1500,
		pending_loyers_total: 0,
		biens,
		recent_loyers: loyers,
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
				body: JSON.stringify([sci])
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

		if (method === 'GET' && (path === '/api/v1/locataires' || path === '/api/v1/locataires/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(locataires)
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/loyers' || path === '/api/v1/loyers/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(loyers)
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
						nom: 'Gérant Principal',
						email: 'gerant@sci.test',
						part: 60,
						role: 'gerant',
						is_account_member: true
					},
					{
						id: 'associe-2',
						id_sci: 'sci-1',
						user_id: null,
						nom: 'Associé Passif',
						email: 'passif@sci.test',
						part: 40,
						role: 'associe',
						is_account_member: false
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

test.describe('Fiche Bien (SCI detail page)', () => {
	test.beforeEach(async ({ page, isMobile }) => {
		test.skip(isMobile, 'Desktop navigation test');
		await installFicheBienMocks(page);
		await seedFakeUserContext(page, { email: 'gerant@sci.test', sciId: 'sci-1' });
	});

	test('SCI detail page displays SCI name and SIREN', async ({ page }) => {
		await page.goto('/scis/sci-1');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('SCI Fiche Test');
		await expect(page.getByText('555666777')).toBeVisible();
	});

	test('SCI detail page shows quick-link cards for biens, associes, regime', async ({
		page
	}) => {
		await page.goto('/scis/sci-1');

		// Quick-link labels should be visible
		await expect(page.getByText('Biens').first()).toBeVisible();
		await expect(page.getByText('Associés').first()).toBeVisible();
		await expect(page.getByText('Régime fiscal').first()).toBeVisible();
	});

	test('SCI biens sub-page loads from fiche', async ({ page }) => {
		await page.goto('/scis/sci-1/biens');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
	});

	test('SCI associes sub-page loads from fiche', async ({ page }) => {
		await page.goto('/scis/sci-1/associes');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
	});

	test('SCI fiscalite sub-page loads from fiche', async ({ page }) => {
		await page.goto('/scis/sci-1/fiscalite');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
	});
});
