/**
 * Showcase: Concu pour Mobile
 * Mobile-first responsive captures: dashboard, sidebar navigation, fiche bien.
 *
 * Uses the "mobile" project from playwright.showcase.config.ts (iPhone 14 viewport).
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

const DASHBOARD_DATA = {
	kpis: {
		total_scis: 2,
		total_biens: 4,
		total_loyers_mois: 6_670,
		total_charges_mois: 770,
		taux_occupation: 100,
		loyers_impayes: 0,
		revenus_annuels: 80_040,
		charges_annuelles: 9_240
	},
	alertes: [
		{
			type: 'bail_expiring',
			message: 'Bail de Emilie Dupont expire dans 45 jours',
			severity: 'warning',
			sci_nom: belleville.nom,
			bien_adresse: '12 rue de Belleville'
		}
	],
	scis: [
		{
			id: 'sci-belleville',
			nom: belleville.nom,
			biens_count: 2,
			loyers_count: 24,
			total_monthly_rent: 2_270,
			user_role: 'gerant'
		}
	],
	activite_recente: [
		{ type: 'loyer_paye', message: 'Loyer de fevrier paye — Fatima Benali', date: '2026-03-05' }
	]
};

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
	tmi: 30
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
	charges_count: 2,
	total_monthly_rent: 2_270,
	total_monthly_property_charges: 270,
	total_recorded_charges: 3_200,
	paid_loyers_total: 27_240,
	pending_loyers_total: 840,
	biens: BIENS,
	recent_loyers: [],
	recent_charges: [],
	fiscalite: [],
	associes: []
};

async function installMobileMocks(page: Page) {
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

		if (method === 'GET' && path === '/api/v1/dashboard') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(DASHBOARD_DATA)
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

		if (method === 'GET' && path.match(/\/api\/v1\/scis\/[^/]+\/biens\/?$/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(BIENS)
			});
			return;
		}

		if (method === 'GET' && path.match(/\/api\/v1\/scis\/[^/]+\/biens\/[^/]+$/)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					...BIENS[0],
					locataires: [
						{
							id: 'loc-1',
							nom: belleville.biens[0].locataire.nom,
							email: belleville.biens[0].locataire.email,
							date_debut: '2023-09-01',
							date_fin: null
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
				})
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/biens' || path === '/api/v1/biens/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(BIENS)
			});
			return;
		}

		if (method === 'GET' && path === '/api/v1/notifications') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify([])
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
// Tests — run only on mobile project
// ---------------------------------------------------------------------------
test.describe.serial('Showcase: Mobile Responsive', () => {
	test.beforeEach(async ({ page }) => {
		if (skipIfNoAuth()) test.skip();
		await installMobileMocks(page);
		await seedShowcaseUser(page, {
			email: MARKETING_USER.email,
			sciId: 'sci-belleville'
		});
	});

	test('capture mobile dashboard', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForTimeout(1500);
		await page.evaluate(() => window.scrollTo(0, 0));
		await capture(page, 'mobile-dashboard');
	});

	test('capture mobile navigation', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForTimeout(1200);

		// Open hamburger / mobile menu
		const hamburger = page.locator(
			'button[aria-label*="menu" i], button[aria-label*="Menu" i], button[aria-label*="nav" i], [data-testid="mobile-menu"], button.hamburger, button.menu-toggle'
		);
		if (await hamburger.first().isVisible()) {
			await hamburger.first().click();
			await page.waitForTimeout(800); // Sidebar slide-in animation
		}

		await capture(page, 'mobile-sidebar');

		// Navigate to biens via sidebar link
		const biensLink = page
			.locator('a, button')
			.filter({ hasText: /biens/i })
			.first();
		if (await biensLink.isVisible()) {
			await biensLink.click();
			await page.waitForTimeout(1200);
		} else {
			await page.goto('/scis/sci-belleville/biens');
			await page.waitForTimeout(1200);
		}

		await page.evaluate(() => window.scrollTo(0, 0));
		await capture(page, 'mobile-biens');
	});

	test('capture mobile fiche bien', async ({ page }) => {
		await page.goto('/scis/sci-belleville/biens/bien-1');
		await page.waitForTimeout(1500);
		await page.evaluate(() => window.scrollTo(0, 0));
		await capture(page, 'mobile-fiche-bien');
	});
});
