import { expect, test } from '@playwright/test';

test.describe('Authentication pages', () => {
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
});
