import { expect, test } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

test.describe('Authentication pages', () => {
	test('protected routes redirect anonymous users to login', async ({ page }) => {
		for (const pathname of [
			'/dashboard',
			'/scis',
			'/biens',
			'/loyers',
			'/account',
			'/account/privacy',
			'/settings',
			'/success'
		]) {
			await page.goto(pathname);
			await page.waitForURL(/\/login(\?|$)/);
			await expect(page).toHaveURL(new RegExp(`/login\\?next=`));
		}
	});

	test('login page exposes magic-link flow', async ({ page }) => {
		await page.goto('/login');

		await expect(page.getByText('Connexion par lien magique')).toBeVisible();

		const emailInput = page.getByPlaceholder('vous@sci.fr');
		await expect(emailInput).toBeVisible();

		const submitButton = page.getByRole('button', { name: 'Recevoir le lien de connexion' });
		await expect(submitButton).toBeDisabled();

		await emailInput.fill('test@example.com');
		await expect(submitButton).toBeEnabled();
	});

	test('register page exposes account-creation flow', async ({ page }) => {
		await page.goto('/register');

		await expect(page.getByText('Créer un compte')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Recevoir le lien de création' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Vous avez déjà un compte?' })).toBeVisible();
	});

	test('connected user opening home is redirected to dashboard', async ({ page }) => {
		await page.route('**/api/v1/**', async (route) => {
			const path = new URL(route.request().url()).pathname;

			if (path === '/api/v1/scis' || path === '/api/v1/scis/') {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify([])
				});
				return;
			}

			if (path === '/api/v1/biens' || path === '/api/v1/biens/') {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify([])
				});
				return;
			}

			if (path === '/api/v1/loyers' || path === '/api/v1/loyers/') {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify([])
				});
				return;
			}

			if (path === '/api/v1/stripe/subscription') {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						plan_key: 'starter',
						plan_name: 'Starter',
						status: 'active',
						mode: 'subscription',
						is_active: true,
						max_scis: 1,
						max_biens: 5,
						current_scis: 0,
						current_biens: 0,
						remaining_scis: 1,
						remaining_biens: 5,
						over_limit: false,
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

		await seedFakeUserContext(page);
		await page.goto('/');
		await page.waitForURL(/\/dashboard$/);
		await expect(page.getByRole('heading', { level: 1 })).toContainText(
			'Dashboard de portefeuille'
		);
	});
});
