import { expect, test } from '@playwright/test';

test('pricing page exposes the three plans', async ({ page }) => {
	await page.goto('/pricing');

	await expect(page.getByText('Tarifs transparents')).toBeVisible();
	await expect(page.getByText('Starter', { exact: true })).toBeVisible();
	await expect(page.getByText('Pro', { exact: true })).toBeVisible();
	await expect(page.getByText('Lifetime', { exact: true })).toBeVisible();

	await expect(page.getByRole('button', { name: 'Choisir Starter' })).toBeVisible();
	await expect(page.getByRole('button', { name: 'Choisir Pro' })).toBeVisible();
	await expect(page.getByRole('button', { name: 'Choisir Lifetime' })).toBeVisible();
});
