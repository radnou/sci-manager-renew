import { page } from 'vitest/browser';
import { describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import Page from './+page.svelte';

describe('/register/+page.svelte', () => {
	it('should render "Créer un compte" title', async () => {
		render(Page);

		const title = page.getByText('Créer un compte', { exact: true });
		await expect.element(title).toBeInTheDocument();
	});

	it('should render register form with email and password fields', async () => {
		render(Page);

		const emailInput = page.getByPlaceholder('vous@sci.fr');
		await expect.element(emailInput).toBeInTheDocument();

		// Two password fields (password + confirm)
		const passwordInputs = page.getByPlaceholder('••••••••');
		await expect.element(passwordInputs.first()).toBeInTheDocument();
	});

	it('should have a link to /login', async () => {
		render(Page);

		const loginLink = page.getByRole('link', { name: /Se connecter/ });
		await expect.element(loginLink).toHaveAttribute('href', '/login');
	});

	it('should display plan description', async () => {
		render(Page);

		const eyebrow = page.getByText('Plan Essentiel — Gratuit');
		await expect.element(eyebrow).toBeInTheDocument();
	});

	it('should have links to CGU and privacy policy', async () => {
		render(Page);

		const cguLink = page.getByRole('link', { name: /CGU/ });
		await expect.element(cguLink).toHaveAttribute('href', '/cgu');

		const privacyLink = page.getByRole('link', { name: /politique de confidentialité/ });
		await expect.element(privacyLink).toHaveAttribute('href', '/confidentialite');
	});
});
