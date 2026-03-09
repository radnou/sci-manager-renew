import { expect, test } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

test.describe('Operations pages', () => {
	test('biens page displays creation workflow shell', async ({ page }) => {
		await seedFakeUserContext(page, { email: 'ops@sci.test', sciId: 'sci-1' });

		await page.goto('/biens');

		await expect(page.getByRole('heading', { name: 'Gestion des biens' })).toBeVisible();
		await expect(page.getByText('Lecture d\u2019actifs avant création')).toBeVisible();
	});

	test('loyers page displays encaissement workflow shell', async ({ page }) => {
		await seedFakeUserContext(page, { email: 'ops@sci.test', sciId: 'sci-1' });

		await page.goto('/loyers');

		await expect(page.getByRole('heading', { name: 'Suivi des loyers' })).toBeVisible();
		await expect(page.getByText(/Journal d.encaissement/)).toBeVisible();
	});
});
