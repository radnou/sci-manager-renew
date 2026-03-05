import { expect, test } from '@playwright/test';

test.describe('Operations pages', () => {
	test('biens page displays creation workflow shell', async ({ page }) => {
		await page.goto('/biens');

		await expect(page.getByRole('heading', { name: 'Gestion des biens' })).toBeVisible();
		await expect(page.getByLabel('ID SCI')).toBeVisible();
		await expect(page.getByLabel('Adresse')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Ajouter le bien' })).toBeVisible();
	});

	test('loyers page blocks submission when no bien is available', async ({ page }) => {
		await page.goto('/loyers');

		await expect(page.getByRole('heading', { name: 'Suivi des loyers' })).toBeVisible();
		await expect(page.getByText('Nouveau loyer')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Ajouter le loyer' })).toBeVisible();
	});
});
