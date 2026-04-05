import { page } from 'vitest/browser';
import { describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import Page from './+page.svelte';

describe('/+page.svelte', () => {
	it('should render headline and primary conversion actions', async () => {
		render(Page);

		const heading = page.getByRole('heading', { level: 1 });
		await expect.element(heading).toBeInTheDocument();
		await expect.element(heading).toHaveTextContent(/Votre SCI sous contrôle/);
		await expect
			.element(page.getByRole('link', { name: /Démarrer maintenant/ }))
			.toHaveAttribute('href', '/pricing');
		await expect
			.element(page.getByRole('link', { name: /Comparer les plans/ }))
			.toHaveAttribute('href', '#pricing');
	});
});
