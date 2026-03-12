import { page } from 'vitest/browser';
import { describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import Page from './+page.svelte';

describe('/forgot-password/+page.svelte', () => {
	it('should render "Mot de passe oublié" title', async () => {
		render(Page);

		const title = page.getByText('Mot de passe oublié', { exact: true });
		await expect.element(title).toBeInTheDocument();
	});

	it('should render email input field', async () => {
		render(Page);

		const emailInput = page.getByPlaceholder('vous@sci.fr');
		await expect.element(emailInput).toBeInTheDocument();
	});

	it('should render submit button', async () => {
		render(Page);

		const submitButton = page.getByRole('button', {
			name: /Envoyer le lien de réinitialisation/
		});
		await expect.element(submitButton).toBeInTheDocument();
	});

	it('should have a link back to /login', async () => {
		render(Page);

		const loginLink = page.getByRole('link', { name: /Se connecter/ });
		await expect.element(loginLink).toHaveAttribute('href', '/login');
	});

	it('should display recovery description', async () => {
		render(Page);

		const description = page.getByText(/Entrez votre adresse email pour recevoir un lien/);
		await expect.element(description).toBeInTheDocument();
	});
});
