import { expect, test, type Page } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

/**
 * Installs API mocks for the onboarding flow.
 * Subscription is active but onboarding is NOT completed — user should land on /onboarding.
 */
async function installOnboardingMocks(page: Page) {
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
					current_scis: 0,
					current_biens: 0,
					remaining_scis: 1,
					remaining_biens: 5,
					over_limit: false,
					onboarding_completed: false,
					features: {}
				})
			});
			return;
		}

		if (method === 'GET' && path === '/api/v1/onboarding/status') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					completed: false,
					sci_created: false,
					bien_created: false,
					bail_created: false,
					notifications_set: false
				})
			});
			return;
		}

		if (method === 'POST' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			const payload = JSON.parse(request.postData() || '{}');
			await route.fulfill({
				status: 201,
				contentType: 'application/json',
				body: JSON.stringify({
					id: 'sci-onboarding',
					nom: payload.nom || 'SCI Onboarding',
					siren: payload.siren || null,
					regime_fiscal: payload.regime_fiscal || 'IR'
				})
			});
			return;
		}

		if (method === 'POST' && (path === '/api/v1/biens' || path === '/api/v1/biens/')) {
			const payload = JSON.parse(request.postData() || '{}');
			await route.fulfill({
				status: 201,
				contentType: 'application/json',
				body: JSON.stringify({
					id: 'bien-onboarding',
					id_sci: payload.id_sci || 'sci-onboarding',
					adresse: payload.adresse,
					ville: payload.ville,
					code_postal: payload.code_postal,
					type_locatif: payload.type_locatif || 'nu',
					loyer_cc: payload.loyer_cc || 0,
					charges: payload.charges || 0,
					tmi: 0
				})
			});
			return;
		}

		if (method === 'POST' && path === '/api/v1/onboarding/complete') {
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

test.describe('Onboarding wizard', () => {
	test.beforeEach(async ({ page, isMobile }) => {
		test.skip(isMobile, 'Desktop navigation test');
		await installOnboardingMocks(page);
		await seedFakeUserContext(page, { email: 'new-user@sci.test' });
	});

	test('onboarding page renders welcome heading and step 1', async ({ page }) => {
		await page.goto('/onboarding');

		await expect(page.getByRole('heading', { level: 1 })).toContainText('Bienvenue sur GererSCI');
		await expect(page.getByText('Configurons votre espace')).toBeVisible();

		// Step 1 content: SCI creation form
		await expect(
			page.getByRole('heading', { level: 2, name: 'Créez votre première SCI' })
		).toBeVisible();
		await expect(page.getByLabel('Nom de la SCI')).toBeVisible();
		await expect(page.getByLabel('SIREN')).toBeVisible();
		await expect(page.getByLabel('Régime fiscal')).toBeVisible();
	});

	test('step progress indicators are visible', async ({ page }) => {
		await page.goto('/onboarding');

		// All 5 step labels should be visible on desktop
		await expect(page.getByText('Votre SCI')).toBeVisible();
		await expect(page.getByText('Votre 1er bien')).toBeVisible();
		await expect(page.getByText('Configuration bail')).toBeVisible();
		await expect(page.getByText('Notifications')).toBeVisible();
		await expect(page.getByText('Bienvenue', { exact: true })).toBeVisible();
	});

	test('step 1 validation requires SCI name', async ({ page }) => {
		await page.goto('/onboarding');

		// Click create without filling name
		await page.getByRole('button', { name: 'Créer la SCI' }).click();

		// Validation error should appear
		await expect(page.getByText('Le nom de la SCI est requis')).toBeVisible();
	});

	test('step 1 advances to step 2 after SCI creation', async ({ page }) => {
		await page.goto('/onboarding');

		// Fill in SCI name and submit
		await page.getByLabel('Nom de la SCI').fill('SCI Mon Test');
		await page.getByRole('button', { name: 'Créer la SCI' }).click();

		// Should advance to step 2
		await expect(
			page.getByRole('heading', { level: 2, name: 'Ajoutez votre premier bien' })
		).toBeVisible();
		await expect(page.getByLabel('Adresse')).toBeVisible();
		await expect(page.getByLabel('Ville')).toBeVisible();
		await expect(page.getByLabel('Code postal')).toBeVisible();
	});

	test('step 2 validation requires address fields', async ({ page }) => {
		await page.goto('/onboarding');

		// Advance past step 1
		await page.getByLabel('Nom de la SCI').fill('SCI Validation');
		await page.getByRole('button', { name: 'Créer la SCI' }).click();
		await expect(page.getByRole('heading', { level: 2 })).toContainText('premier bien');

		// Click add without filling required fields
		await page.getByRole('button', { name: 'Ajouter le bien' }).click();

		// Validation error
		await expect(page.getByText('adresse, la ville et le code postal sont requis')).toBeVisible();
	});

	test('full onboarding flow progresses through all steps', async ({ page }) => {
		test.slow();
		await page.goto('/onboarding');

		// Step 1: Create SCI
		await page.getByLabel('Nom de la SCI').fill('SCI Parcours Complet');
		await page.getByRole('button', { name: 'Créer la SCI' }).click();

		// Step 2: Add bien
		await expect(page.getByRole('heading', { level: 2 })).toContainText('premier bien');
		await page.getByLabel('Adresse').fill('1 rue du Test');
		await page.getByLabel('Ville').fill('Paris');
		await page.getByLabel('Code postal').fill('75001');
		await page.getByRole('button', { name: 'Ajouter le bien' }).click();

		// Step 3: Bail configuration (skip)
		await expect(page.getByRole('heading', { level: 2 })).toContainText('Configuration du bail');
		await page.getByRole('button', { name: 'Continuer' }).click();

		// Step 4: Notifications
		await expect(page.getByRole('heading', { level: 2 })).toContainText('Préférences de notifications');
		await expect(page.getByText('alertes par email')).toBeVisible();
		await page.getByRole('button', { name: 'Continuer' }).click();

		// Step 5: Welcome / completion
		await expect(page.getByRole('heading', { level: 2 })).toContainText('Tout est prêt');
		await expect(page.getByRole('button', { name: 'Accéder au dashboard' })).toBeVisible();
	});
});
