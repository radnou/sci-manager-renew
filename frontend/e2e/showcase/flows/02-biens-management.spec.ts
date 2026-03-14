/**
 * Showcase: Gerer ses Biens en un Coup d'Oeil
 * Grid view of biens + fiche bien tab navigation with rich data.
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

const BIENS = belleville.biens.map((b, i) => ({
	id: `bien-${i + 1}`,
	id_sci: 'sci-belleville',
	adresse: b.adresse,
	ville: b.ville,
	code_postal: b.code_postal,
	type_locatif: b.type_locatif,
	surface_m2: b.surface_m2,
	nb_pieces: b.nb_pieces,
	loyer_cc: b.loyer_cc,
	charges: b.charges,
	dpe_classe: b.dpe_classe,
	tmi: 30,
	statut: 'loue',
	bail_actif: { id: `bail-${i + 1}`, date_debut: '2023-09-01', date_fin: '2026-04-28' },
	rentabilite_brute: 8.2 - i * 0.5,
	cashflow_annuel: 9_840 - i * 2_000
}));

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
	charges_count: 4,
	total_monthly_rent: 2_270,
	total_monthly_property_charges: 270,
	total_recorded_charges: 3_200,
	paid_loyers_total: 27_240,
	pending_loyers_total: 840,
	biens: BIENS,
	recent_loyers: [
		{
			id: 'loyer-1',
			id_bien: 'bien-1',
			id_sci: 'sci-belleville',
			id_locataire: 'loc-1',
			date_loyer: '2026-03-01',
			montant: 1_430,
			statut: 'paye',
			quitus_genere: true
		},
		{
			id: 'loyer-2',
			id_bien: 'bien-2',
			id_sci: 'sci-belleville',
			id_locataire: 'loc-2',
			date_loyer: '2026-03-01',
			montant: 840,
			statut: 'en_attente',
			quitus_genere: false
		},
		{
			id: 'loyer-3',
			id_bien: 'bien-1',
			id_sci: 'sci-belleville',
			id_locataire: 'loc-1',
			date_loyer: '2026-02-01',
			montant: 1_430,
			statut: 'paye',
			quitus_genere: true
		}
	],
	recent_charges: [
		{ id: 'charge-1', id_bien: 'bien-1', type: 'copropriete', montant: 180, date: '2026-01-15' },
		{
			id: 'charge-2',
			id_bien: 'bien-1',
			type: 'taxe_fonciere',
			montant: 1_200,
			date: '2025-10-15'
		}
	],
	fiscalite: [],
	associes: belleville.associes.map((a, i) => ({
		id: `associe-${i + 1}`,
		nom: a.nom,
		email: a.email,
		part: a.part,
		role: a.role,
		user_id: i === 0 ? 'user-showcase-001' : `user-other-${i}`
	}))
};

const LOYERS_BIEN_1 = Array.from({ length: 12 }, (_, i) => {
	const d = new Date(2026, 2 - i, 1);
	return {
		id: `loyer-b1-${i}`,
		id_bien: 'bien-1',
		id_sci: 'sci-belleville',
		id_locataire: 'loc-1',
		date_loyer: d.toISOString().slice(0, 10),
		montant: 1_430,
		statut: i === 0 ? 'en_attente' : 'paye',
		quitus_genere: i > 0
	};
});

const CHARGES_BIEN_1 = [
	{
		id: 'charge-b1-1',
		id_bien: 'bien-1',
		type: 'copropriete',
		montant: 180,
		frequence: 'mensuel',
		date: '2026-01-15'
	},
	{
		id: 'charge-b1-2',
		id_bien: 'bien-1',
		type: 'taxe_fonciere',
		montant: 1_200,
		frequence: 'annuel',
		date: '2025-10-15'
	},
	{
		id: 'charge-b1-3',
		id_bien: 'bien-1',
		type: 'assurance_pno',
		montant: 350,
		frequence: 'annuel',
		date: '2025-09-01'
	}
];

const LOCATAIRES = [
	{
		id: 'loc-1',
		id_bien: 'bien-1',
		id_sci: 'sci-belleville',
		nom: belleville.biens[0].locataire.nom,
		email: belleville.biens[0].locataire.email,
		date_debut: '2023-09-01',
		date_fin: '2026-04-28'
	}
];

const RENTABILITE = {
	rentabilite_brute: 8.2,
	rentabilite_nette: 5.9,
	cashflow_mensuel: 820,
	cashflow_annuel: 9_840,
	revenus_annuels: 17_160,
	charges_annuelles: 7_320,
	prix_acquisition: 210_000
};

async function installBiensMocks(page: Page) {
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

		// Biens list
		if (
			method === 'GET' &&
			path.match(/\/api\/v1\/scis\/[^/]+\/biens\/?$/)
		) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(BIENS)
			});
			return;
		}

		// Single bien detail
		if (method === 'GET' && path.match(/\/api\/v1\/scis\/[^/]+\/biens\/[^/]+$/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					...BIENS[0],
					locataires: LOCATAIRES,
					baux: [
						{
							id: 'bail-1',
							id_bien: 'bien-1',
							date_debut: '2023-09-01',
							date_fin: '2026-04-28',
							loyer_hc: 1_250,
							charges_provisions: 180,
							type_bail: 'nu',
							locataires: LOCATAIRES
						}
					]
				})
			});
			return;
		}

		// Loyers for a bien
		if (method === 'GET' && path.match(/\/api\/v1\/scis\/[^/]+\/biens\/[^/]+\/loyers/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(LOYERS_BIEN_1)
			});
			return;
		}

		// Charges for a bien
		if (method === 'GET' && path.match(/\/api\/v1\/scis\/[^/]+\/biens\/[^/]+\/charges/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(CHARGES_BIEN_1)
			});
			return;
		}

		// Rentabilite
		if (method === 'GET' && path.match(/\/api\/v1\/scis\/[^/]+\/biens\/[^/]+\/rentabilite/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(RENTABILITE)
			});
			return;
		}

		// Locataires
		if (method === 'GET' && path.match(/\/api\/v1\/locataires/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(LOCATAIRES)
			});
			return;
		}

		// Biens (global)
		if (method === 'GET' && (path === '/api/v1/biens' || path === '/api/v1/biens/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(BIENS)
			});
			return;
		}

		// Default
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
test.describe.serial('Showcase: Biens Management', () => {
	test.beforeEach(async ({ page }) => {
		if (skipIfNoAuth()) test.skip();
		await installBiensMocks(page);
		await seedShowcaseUser(page, {
			email: MARKETING_USER.email,
			sciId: 'sci-belleville'
		});
	});

	test('capture biens grid', async ({ page }) => {
		await page.goto('/scis/sci-belleville/biens');
		await page.waitForTimeout(1200);
		await page.evaluate(() => window.scrollTo(0, 0));
		await capture(page, 'biens-grid');
	});

	test('capture fiche bien tabs', async ({ page }) => {
		// Navigate to first bien
		await page.goto('/scis/sci-belleville/biens/bien-1');
		await page.waitForTimeout(1200);
		await page.evaluate(() => window.scrollTo(0, 0));
		await capture(page, 'fiche-identite');

		// Click Bail tab
		const bailTab = page.locator('button, a, [role="tab"]').filter({ hasText: /bail/i }).first();
		if (await bailTab.isVisible()) {
			await bailTab.click();
			await page.waitForTimeout(800);
			await capture(page, 'fiche-bail');
		}

		// Click Loyers tab
		const loyersTab = page
			.locator('button, a, [role="tab"]')
			.filter({ hasText: /loyers/i })
			.first();
		if (await loyersTab.isVisible()) {
			await loyersTab.click();
			await page.waitForTimeout(800);
			await capture(page, 'fiche-loyers');
		}

		// Click Charges tab
		const chargesTab = page
			.locator('button, a, [role="tab"]')
			.filter({ hasText: /charges/i })
			.first();
		if (await chargesTab.isVisible()) {
			await chargesTab.click();
			await page.waitForTimeout(800);
			await capture(page, 'fiche-charges');
		}

		// Click Rentabilite tab
		const rentaTab = page
			.locator('button, a, [role="tab"]')
			.filter({ hasText: /rentabilit/i })
			.first();
		if (await rentaTab.isVisible()) {
			await rentaTab.click();
			await page.waitForTimeout(800);
			await capture(page, 'fiche-rentabilite');
		}
	});
});
