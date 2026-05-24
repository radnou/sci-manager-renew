import { page } from 'vitest/browser';
import { describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import Page from './+page.svelte';

describe('/+page.svelte', () => {
	it('should render headline and primary conversion actions', async () => {
		render(Page);

		const heading = page.getByRole('heading', { level: 1 });
		await expect.element(heading).toBeInTheDocument();
		await expect.element(heading).toHaveTextContent(/Gérez votre/i);
		await expect
			.element(page.getByRole('button', { name: /Essayer gratuitement/i }))
			.toBeInTheDocument();
		await expect
			.element(page.getByRole('button', { name: /Voir la présentation/i }))
			.toBeInTheDocument();
	});
});

