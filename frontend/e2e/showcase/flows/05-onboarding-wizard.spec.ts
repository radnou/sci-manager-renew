/**
 * Showcase: Onboarding Sans Friction
 * Full onboarding wizard with slow, deliberate typing for video capture.
 *
 * NOT a functional test: focuses on visual quality, slow interactions, named screenshots.
 */
import { test, type Page } from '@playwright/test';

import { MARKETING_SCIS, MARKETING_USER } from '../seed/marketing-data';
import { capture, seedShowcaseUser, skipIfNoAuth } from '../helpers/showcase-auth';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

const belleville = MARKETING_SCIS[0];

const SUBSCRIPTION_ONBOARDING = {
	plan_key: 'starter',
	plan_name: 'Starter',
	status: 'active',
	mode: 'subscription',
	is_active: true,
	entitlements_version: 1,
	max_scis: 1,
	max_biens: 5,
	current_scis: 0,
	current_biens: 0,
	remaining_scis: 1,
	remaining_biens: 5,
	over_limit: false,
	onboarding_completed: false,
	features: {}
};

async function installOnboardingMocks(page: Page) {
	let onboardingStep = 0;

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
				body: JSON.stringify(SUBSCRIPTION_ONBOARDING)
			});
			return;
		}

		if (method === 'GET' && path === '/api/v1/onboarding/status') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					completed: onboardingStep >= 4,
					sci_created: onboardingStep >= 1,
					bien_created: onboardingStep >= 2,
					bail_created: onboardingStep >= 3,
					notifications_set: onboardingStep >= 4
				})
			});
			return;
		}

		// SCI creation
		if (method === 'POST' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			onboardingStep = 1;
			const payload = JSON.parse(request.postData() || '{}');
			await route.fulfill({
				status: 201,
				contentType: 'application/json',
				body: JSON.stringify({
					id: 'sci-belleville',
					nom: payload.nom || belleville.nom,
					siren: payload.siren || belleville.siren,
					regime_fiscal: payload.regime_fiscal || belleville.regime_fiscal
				})
			});
			return;
		}

		// Bien creation
		if (method === 'POST' && (path === '/api/v1/biens' || path === '/api/v1/biens/')) {
			onboardingStep = 2;
			const payload = JSON.parse(request.postData() || '{}');
			await route.fulfill({
				status: 201,
				contentType: 'application/json',
				body: JSON.stringify({
					id: 'bien-1',
					id_sci: 'sci-belleville',
					adresse: payload.adresse || belleville.biens[0].adresse,
					ville: payload.ville || belleville.biens[0].ville,
					code_postal: payload.code_postal || belleville.biens[0].code_postal,
					type_locatif: payload.type_locatif || 'nu',
					loyer_cc: payload.loyer_cc || 0,
					charges: payload.charges || 0,
					tmi: 0
				})
			});
			return;
		}

		// Onboarding complete
		if (method === 'POST' && path === '/api/v1/onboarding/complete') {
			onboardingStep = 4;
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ completed: true })
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(onboardingStep >= 1 ? [{ id: 'sci-belleville', nom: belleville.nom }] : [])
			});
			return;
		}

		// Dashboard data (shown after onboarding completion)
		if (method === 'GET' && path === '/api/v1/dashboard') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					kpis: {
						total_scis: 1,
						total_biens: 1,
						total_loyers_mois: 0,
						total_charges_mois: 0,
						taux_occupation: 0,
						loyers_impayes: 0,
						revenus_annuels: 0,
						charges_annuelles: 0
					},
					alertes: [],
					scis: [{ id: 'sci-belleville', nom: belleville.nom, biens_count: 1, loyers_count: 0, total_monthly_rent: 0, user_role: 'gerant' }],
					activite_recente: []
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

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
test.describe.serial('Showcase: Onboarding Wizard', () => {
	test.beforeEach(async ({ page }) => {
		if (skipIfNoAuth()) test.skip();
		await installOnboardingMocks(page);
		await seedShowcaseUser(page, { email: MARKETING_USER.email });
	});

	test('capture full onboarding flow', async ({ page }) => {
		test.slow(); // Allow extra time for deliberate typing

		await page.goto('/onboarding');
		await page.waitForTimeout(1200);

		// ----- Step 1: Create SCI -----
		const sciNameInput = page.getByLabel('Nom de la SCI');
		if (await sciNameInput.isVisible()) {
			await sciNameInput.click();
			await page.type('[id="nom"], [name="nom"], label:has-text("Nom de la SCI") + input, input', belleville.nom, {
				delay: 50
			}).catch(() => sciNameInput.fill(belleville.nom));
		}

		// Fill SIREN if visible
		const sirenInput = page.getByLabel('SIREN');
		if (await sirenInput.isVisible()) {
			await sirenInput.fill(belleville.siren);
		}

		// Select regime fiscal if visible
		const regimeSelect = page.getByLabel('Régime fiscal');
		if (await regimeSelect.isVisible()) {
			await regimeSelect.selectOption(belleville.regime_fiscal).catch(() => {});
		}

		await page.waitForTimeout(600);
		await capture(page, 'onboarding-step1');

		// Submit step 1
		const createSciBtn = page.getByRole('button', { name: /cr[eé]er la sci/i });
		if (await createSciBtn.isVisible()) {
			await createSciBtn.click();
			await page.waitForTimeout(1000);
		}

		// ----- Step 2: Add Bien -----
		const adresseInput = page.getByLabel('Adresse');
		if (await adresseInput.isVisible()) {
			await adresseInput.click();
			await page.type('[id="adresse"], [name="adresse"], label:has-text("Adresse") + input, input[placeholder*="adresse" i]', belleville.biens[0].adresse, {
				delay: 50
			}).catch(() => adresseInput.fill(belleville.biens[0].adresse));
		}

		const villeInput = page.getByLabel('Ville');
		if (await villeInput.isVisible()) {
			await villeInput.fill(belleville.biens[0].ville);
		}

		const cpInput = page.getByLabel('Code postal');
		if (await cpInput.isVisible()) {
			await cpInput.fill(belleville.biens[0].code_postal);
		}

		await page.waitForTimeout(600);
		await capture(page, 'onboarding-step2');

		// Submit step 2
		const addBienBtn = page.getByRole('button', { name: /ajouter le bien/i });
		if (await addBienBtn.isVisible()) {
			await addBienBtn.click();
			await page.waitForTimeout(1000);
		}

		// ----- Step 3: Bail configuration -----
		await page.waitForTimeout(600);
		await capture(page, 'onboarding-step3');

		// Click Continue (bail step may be skippable)
		const continueBtn3 = page.getByRole('button', { name: /continuer/i });
		if (await continueBtn3.isVisible()) {
			await continueBtn3.click();
			await page.waitForTimeout(1000);
		}

		// ----- Step 4: Notifications -----
		// Toggle notification switches for visual effect
		const toggles = page.locator('input[type="checkbox"], button[role="switch"]');
		const toggleCount = await toggles.count();
		for (let i = 0; i < Math.min(toggleCount, 3); i++) {
			await toggles.nth(i).click().catch(() => {});
			await page.waitForTimeout(300);
		}

		await page.waitForTimeout(600);
		await capture(page, 'onboarding-step4');

		// Complete onboarding
		const continueBtn4 = page.getByRole('button', { name: /continuer/i });
		if (await continueBtn4.isVisible()) {
			await continueBtn4.click();
			await page.waitForTimeout(1000);
		}

		// ----- Step 5: Completion -----
		const dashboardBtn = page.getByRole('button', { name: /acc[eé]der au dashboard|terminer/i });
		if (await dashboardBtn.isVisible()) {
			await page.waitForTimeout(600);
			await capture(page, 'onboarding-complete');
		} else {
			// Capture whatever the final state is
			await page.waitForTimeout(600);
			await capture(page, 'onboarding-complete');
		}
	});
});
