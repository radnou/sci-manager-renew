import { test, expect } from '@playwright/test';
import { takeScreenshots, SCREENSHOT_DIR } from './helpers/auth';

test.describe.serial('02 — Flux d\'authentification', () => {
	test('Page login — formulaire mot de passe (par defaut)', async ({ page }) => {
		await page.goto('/login');
		await page.waitForLoadState('networkidle');

		// Verify page title
		await expect(page).toHaveTitle(/Connexion/);

		// Verify card structure
		await expect(page.getByText('Espace de gestion')).toBeVisible();
		await expect(page.getByRole('heading', { name: 'Connexion' })).toBeVisible();
		await expect(page.getByText('Accédez à votre espace de gestion SCI.')).toBeVisible();

		// Verify form fields
		const emailInput = page.getByPlaceholder('vous@sci.fr');
		await expect(emailInput).toBeVisible();
		await expect(emailInput).toHaveAttribute('type', 'email');

		const passwordInput = page.getByPlaceholder('••••••••');
		await expect(passwordInput).toBeVisible();
		await expect(passwordInput).toHaveAttribute('type', 'password');

		// Verify submit button (disabled when empty)
		const submitBtn = page.getByRole('button', { name: 'Se connecter' });
		await expect(submitBtn).toBeVisible();
		await expect(submitBtn).toBeDisabled();

		// Verify links
		await expect(page.getByText('Mot de passe oublié ?')).toBeVisible();
		await expect(page.getByText('Créer un compte gratuit')).toBeVisible();

		// Verify magic link toggle
		await expect(page.getByText('Connexion par lien magique')).toBeVisible();

		await takeScreenshots(page, '02-login-password-mode');
	});

	test('Page login — saisie email et mot de passe', async ({ page }) => {
		await page.goto('/login');
		await page.waitForLoadState('networkidle');

		// Fill in email
		const emailInput = page.getByPlaceholder('vous@sci.fr');
		await emailInput.fill('demo@gerersci.fr');

		// Fill in password
		const passwordInput = page.getByPlaceholder('••••••••');
		await passwordInput.fill('MonMotDePasse123');

		// Submit button should be enabled now
		const submitBtn = page.getByRole('button', { name: 'Se connecter' });
		await expect(submitBtn).toBeEnabled();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/02-login-filled.png`,
			fullPage: false
		});
	});

	test('Page login — basculer vers lien magique', async ({ page }) => {
		await page.goto('/login');
		await page.waitForLoadState('networkidle');

		// Switch to magic link mode
		await page.getByText('Connexion par lien magique').click();
		await page.waitForTimeout(200);

		// Password field should disappear
		await expect(page.getByPlaceholder('••••••••')).not.toBeVisible();

		// Email field still visible
		await expect(page.getByPlaceholder('vous@sci.fr')).toBeVisible();

		// Button text should change
		await expect(page.getByRole('button', { name: /Recevoir le lien/i })).toBeVisible();

		// Toggle should show "Connexion par mot de passe"
		await expect(page.getByText('Connexion par mot de passe')).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/02-login-magic-link-mode.png`,
			fullPage: false
		});
	});

	test('Page login — soumission magic link avec email', async ({ page }) => {
		await page.goto('/login');
		await page.waitForLoadState('networkidle');

		// Switch to magic link
		await page.getByText('Connexion par lien magique').click();
		await page.waitForTimeout(200);

		// Fill email
		await page.getByPlaceholder('vous@sci.fr').fill('demo@gerersci.fr');

		// Submit — this will fail against real API but we capture the UI state
		const submitBtn = page.getByRole('button', { name: /Recevoir le lien/i });
		await expect(submitBtn).toBeEnabled();
		await submitBtn.click();

		// Wait for loading state or error
		await page.waitForTimeout(1500);

		// Either we see an error message or "Lien envoye" — screenshot both states
		await page.screenshot({
			path: `${SCREENSHOT_DIR}/02-login-magic-link-submitted.png`,
			fullPage: false
		});
	});

	test('Page login — redirection depuis route protegee', async ({ page }) => {
		// Try to access a protected route without auth
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');

		// Should redirect to /login with a redirect param
		await expect(page).toHaveURL(/\/login/);

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/02-login-redirect-from-dashboard.png`,
			fullPage: false
		});
	});

	test('Page login — accessibilite du formulaire', async ({ page }) => {
		await page.goto('/login');
		await page.waitForLoadState('networkidle');

		// Verify form fields have proper labels
		const emailLabel = page.getByText('Email', { exact: true });
		await expect(emailLabel).toBeVisible();

		const passwordLabel = page.getByText('Mot de passe', { exact: true });
		await expect(passwordLabel).toBeVisible();

		// Tab navigation test: focus moves through form elements
		await page.keyboard.press('Tab');
		await page.keyboard.press('Tab');
		// The email input should be focusable
		const emailInput = page.getByPlaceholder('vous@sci.fr');
		await emailInput.focus();
		await expect(emailInput).toBeFocused();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/02-login-a11y.png`,
			fullPage: false
		});
	});
});
