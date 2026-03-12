import { page } from 'vitest/browser';
import { describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import Page from './+page.svelte';

describe('/login/+page.svelte', () => {
	it('should render "Connexion" title', async () => {
		render(Page);

		const title = page.getByText('Connexion', { exact: true });
		await expect.element(title).toBeInTheDocument();
	});

	it('should render email input field', async () => {
		render(Page);

		const emailInput = page.getByPlaceholder('vous@sci.fr');
		await expect.element(emailInput).toBeInTheDocument();
	});

	it('should render password input field in password mode', async () => {
		render(Page);

		const passwordInput = page.getByPlaceholder('••••••••');
		await expect.element(passwordInput).toBeInTheDocument();
	});

	it('should have a link to /register', async () => {
		render(Page);

		const registerLink = page.getByRole('link', { name: /Créer un compte gratuit/ });
		await expect.element(registerLink).toHaveAttribute('href', '/register');
	});

	it('should have a link to /forgot-password', async () => {
		render(Page);

		const forgotLink = page.getByRole('link', { name: /Mot de passe oublié/ });
		await expect.element(forgotLink).toHaveAttribute('href', '/forgot-password');
	});

	it('should toggle between password and magic-link mode', async () => {
		render(Page);

		// Initially in password mode — should show magic link toggle button
		const magicLinkButton = page.getByRole('button', { name: /Connexion par lien magique/ });
		await expect.element(magicLinkButton).toBeInTheDocument();

		// Click to switch to magic-link mode
		await magicLinkButton.click();

		// Now should show password mode toggle button
		const passwordButton = page.getByRole('button', { name: /Connexion par mot de passe/ });
		await expect.element(passwordButton).toBeInTheDocument();

		// Password field should no longer be visible
		const passwordInput = page.getByPlaceholder('••••••••');
		await expect.element(passwordInput).not.toBeInTheDocument();

		// Submit button text should change
		const submitButton = page.getByRole('button', { name: /Recevoir le lien de connexion/ });
		await expect.element(submitButton).toBeInTheDocument();
	});
});
