import { page } from 'vitest/browser';
import { describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import Page from './+page.svelte';

describe('/+page.svelte', () => {
	it('should render headline and primary conversion actions', async () => {
		render(Page);

		const heading = page.getByRole('heading', { level: 1 });
		await expect.element(heading).toBeInTheDocument();
		await expect.element(heading).toHaveTextContent(/Pilotez votre SCI/);
		await expect.element(
			page.getByRole('link', { name: /Créer un compte/ })
		).toHaveAttribute('href', '/register');
		await expect.element(
			page.getByRole('link', { name: /Voir les tarifs/ })
		).toHaveAttribute('href', '#pricing');
	});
});
