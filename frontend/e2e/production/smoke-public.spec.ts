import { test, expect } from '@playwright/test';

const apiBaseUrl = process.env.E2E_API_BASE_URL || 'https://api.gerersci.fr';

test.describe('Smoke prod public', () => {
	test('health readiness est ready', async ({ request }) => {
		const response = await request.get(`${apiBaseUrl}/health/ready`);
		expect(response.ok()).toBeTruthy();

		const payload = await response.json();
		expect(payload.status).toBe('ready');
		expect(payload.summary.ready_for_traffic).toBe(true);
	});

	test('landing, login, register et simulateur chargent', async ({ page }) => {
		for (const path of ['/', '/login', '/register', '/simulateur-cerfa']) {
			await page.goto(path);
			await page.waitForLoadState('networkidle');
			await expect(page.locator('body')).toBeVisible();
		}
	});

	test('pricing charge et le checkout invite renvoie un flux valide', async ({ page, request }) => {
		await page.goto('/pricing');
		await page.waitForLoadState('networkidle');

		await expect(page.getByRole('button', { name: /Démarrer pour 19/i })).toBeVisible();

		const response = await request.post(`${apiBaseUrl}/api/v1/stripe/create-guest-checkout`, {
			data: { plan_key: 'starter', billing_period: 'month' }
		});

		expect(response.ok()).toBeTruthy();
		const payload = await response.json();
		expect(typeof payload.url).toBe('string');
		expect(payload.url).toContain('stripe');
	});
});
