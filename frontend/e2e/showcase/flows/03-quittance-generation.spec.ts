/**
 * Showcase: Quittances en 1 Clic
 * Demonstrates the one-click quittance generation flow.
 *
 * NOT a functional test: focuses on visual quality, slow interactions, named screenshots.
 */
import { test, type Page } from '@playwright/test';

import { MARKETING_SCIS, MARKETING_USER } from '../seed/marketing-data';
import { capture, seedShowcaseUser, skipIfNoAuth, PRO_SUBSCRIPTION } from '../helpers/showcase-auth';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

const belleville = MARKETING_SCIS[0];
const SUBSCRIPTION = PRO_SUBSCRIPTION;

const BIEN = {
	id: 'bien-1',
	id_sci: 'sci-belleville',
	adresse: belleville.biens[0].adresse,
	ville: belleville.biens[0].ville,
	code_postal: belleville.biens[0].code_postal,
	type_locatif: belleville.biens[0].type_locatif,
	surface_m2: belleville.biens[0].surface_m2,
	nb_pieces: belleville.biens[0].nb_pieces,
	loyer_cc: belleville.biens[0].loyer_cc,
	charges: belleville.biens[0].charges,
	dpe_classe: belleville.biens[0].dpe_classe,
	tmi: 30,
	statut: 'loue',
	rentabilite_brute: 8.2,
	cashflow_annuel: 9_840,
	locataires: [
		{
			id: 'loc-1',
			nom: belleville.biens[0].locataire.nom,
			email: belleville.biens[0].locataire.email,
			date_debut: '2023-09-01',
			date_fin: '2026-04-28'
		}
	],
	baux: [
		{
			id: 'bail-1',
			id_bien: 'bien-1',
			date_debut: '2023-09-01',
			date_fin: '2026-04-28',
			loyer_hc: 1_250,
			charges_provisions: 180,
			type_bail: 'nu'
		}
	]
};

const LOYERS = [
	{
		id: 'loyer-feb',
		id_bien: 'bien-1',
		id_sci: 'sci-belleville',
		id_locataire: 'loc-1',
		date_loyer: '2026-02-01',
		montant: 1_430,
		statut: 'paye',
		quitus_genere: false
	},
	{
		id: 'loyer-jan',
		id_bien: 'bien-1',
		id_sci: 'sci-belleville',
		id_locataire: 'loc-1',
		date_loyer: '2026-01-01',
		montant: 1_430,
		statut: 'paye',
		quitus_genere: true
	}
];

const SCI_DETAIL = {
	id: 'sci-belleville',
	nom: belleville.nom,
	siren: belleville.siren,
	regime_fiscal: belleville.regime_fiscal,
	statut: 'exploitation',
	associes_count: 2,
	biens_count: 2,
	loyers_count: 24,
	user_role: 'gerant',
	user_part: 60,
	biens: [BIEN],
	recent_loyers: LOYERS,
	recent_charges: [],
	fiscalite: [],
	associes: [
		{ id: 'associe-1', nom: 'Sophie Moreau', email: 'sophie.moreau@gerersci.fr', part: 60, role: 'gerant', user_id: 'user-showcase-001' },
		{ id: 'associe-2', nom: 'Marc Moreau', email: 'marc.moreau@gmail.com', part: 40, role: 'associe', user_id: 'user-other-1' }
	]
};

async function installQuittanceMocks(page: Page) {
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
				body: JSON.stringify(SUBSCRIPTION)
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([SCI_DETAIL])
			});
			return;
		}

		if (method === 'GET' && path.match(/\/api\/v1\/scis\/[^/]+$/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(SCI_DETAIL)
			});
			return;
		}

		if (method === 'GET' && path.match(/\/api\/v1\/scis\/[^/]+\/biens\/[^/]+$/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(BIEN)
			});
			return;
		}

		if (method === 'GET' && path.match(/\/api\/v1\/scis\/[^/]+\/biens\/[^/]+\/loyers/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(LOYERS)
			});
			return;
		}

		// Quittance generation endpoint — return success with fake PDF URL
		if (method === 'POST' && path.match(/\/api\/v1\/quitus/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					success: true,
					url: 'https://storage.gerersci.fr/quittances/quittance-belleville-2026-02.pdf',
					filename: 'quittance-belleville-2026-02.pdf'
				})
			});
			return;
		}

		if (method === 'GET' && path.match(/\/api\/v1\/locataires/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([
					{
						id: 'loc-1',
						id_bien: 'bien-1',
						id_sci: 'sci-belleville',
						nom: belleville.biens[0].locataire.nom,
						email: belleville.biens[0].locataire.email,
						date_debut: '2023-09-01',
						date_fin: null
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

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
test.describe.serial('Showcase: Quittance Generation', () => {
	test.beforeEach(async ({ page }) => {
		if (skipIfNoAuth()) test.skip();
		await installQuittanceMocks(page);
		await seedShowcaseUser(page, {
			email: MARKETING_USER.email,
			sciId: 'sci-belleville'
		});
	});

	test('capture quittance generation flow', async ({ page }) => {
		// Navigate to fiche bien
		await page.goto('/scis/sci-belleville/biens/bien-1');
		await page.waitForTimeout(1200);

		// Click Loyers tab
		const loyersTab = page
			.locator('button, a, [role="tab"]')
			.filter({ hasText: /loyers/i })
			.first();
		if (await loyersTab.isVisible()) {
			await loyersTab.click();
			await page.waitForTimeout(800);
		}

		// Screenshot before generation — show the generate button
		await capture(page, 'loyers-with-button');

		// Click the generate quittance button
		const genButton = page
			.locator('button')
			.filter({ hasText: /quittance|generer|g[eé]n[eé]rer/i })
			.first();
		if (await genButton.isVisible()) {
			await genButton.click();
			await page.waitForTimeout(1500); // Wait for API response + success feedback
		}

		await capture(page, 'quittance-generated');
	});
});
