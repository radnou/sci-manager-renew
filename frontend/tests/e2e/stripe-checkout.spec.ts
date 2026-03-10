import { expect, test } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

test.describe('Stripe checkout redirect flow', () => {
	test('clicking a plan CTA calls create-checkout-session with correct payload', async ({
		page,
		isMobile
	}) => {
		test.skip(isMobile, 'Desktop pricing page test');

		let checkoutPayload: Record<string, unknown> | null = null;
		const fakeStripeUrl = 'https://checkout.stripe.com/c/pay_test_fakeSessionId123';

		await seedFakeUserContext(page, { email: 'checkout@sci.test' });

		await page.route('**/*', async (route) => {
			const request = route.request();
			const method = request.method();
			const url = request.url();

			if (!url.includes('/api/v1/') && !url.includes('checkout.stripe.com')) {
				await route.continue();
				return;
			}

			const path = new URL(url).pathname;

			if (method === 'OPTIONS') {
				await route.fulfill({ status: 204, headers: CORS_HEADERS });
				return;
			}

			if (url.includes('checkout.stripe.com')) {
				await route.fulfill({
					status: 200,
					contentType: 'text/html',
					body: '<html><body><h1>Stripe Checkout</h1></body></html>'
				});
				return;
			}

			if (method === 'POST' && path.includes('/stripe/create-checkout-session')) {
				checkoutPayload = JSON.parse(request.postData() || '{}');
				await route.fulfill({
					status: 200,
					headers: CORS_HEADERS,
					contentType: 'application/json',
					body: JSON.stringify({ url: fakeStripeUrl })
				});
				return;
			}

			await route.fulfill({
				status: 200,
				headers: CORS_HEADERS,
				contentType: 'application/json',
				body: JSON.stringify([])
			});
		});

		await page.goto('/pricing');
		await expect(page.getByText('Tarifs transparents')).toBeVisible();
		// Wait for Svelte 5 hydration and all initial network requests to complete
		await page.waitForLoadState('networkidle');

		const proButton = page.getByRole('button', { name: 'Choisir Pro' });
		await expect(proButton).toBeVisible();

		// Click and wait for navigation to Stripe
		await Promise.all([
			page.waitForURL(/checkout\.stripe\.com/, { timeout: 15000 }),
			proButton.click()
		]);

		expect(checkoutPayload).not.toBeNull();
		expect(checkoutPayload).toMatchObject({
			plan_key: 'pro',
			mode: 'subscription'
		});
	});

	test('checkout failure shows error toast', async ({ page, isMobile }) => {
		test.skip(isMobile, 'Desktop pricing page test');

		await seedFakeUserContext(page, { email: 'checkout-fail@sci.test' });

		await page.route('**/*', async (route) => {
			const request = route.request();
			const method = request.method();
			const url = request.url();

			if (!url.includes('/api/v1/')) {
				await route.continue();
				return;
			}

			const path = new URL(url).pathname;

			if (method === 'OPTIONS') {
				await route.fulfill({ status: 204, headers: CORS_HEADERS });
				return;
			}

			if (method === 'POST' && path.includes('/stripe/create-checkout-session')) {
				await route.fulfill({
					status: 500,
					headers: CORS_HEADERS,
					contentType: 'application/json',
					body: JSON.stringify({
						error: 'Stripe service unavailable',
						code: 'stripe_error'
					})
				});
				return;
			}

			await route.fulfill({
				status: 200,
				headers: CORS_HEADERS,
				contentType: 'application/json',
				body: JSON.stringify([])
			});
		});

		await page.goto('/pricing');
		await expect(page.getByText('Tarifs transparents')).toBeVisible();
		// Wait for Svelte 5 hydration and all initial network requests to complete
		await page.waitForLoadState('networkidle');

		const starterButton = page.getByRole('button', { name: 'Choisir Starter' });
		await expect(starterButton).toBeVisible();

		// Playwright native click triggers Svelte 5 event delegation (isTrusted=true)
		await starterButton.click();

		// Error toast should appear
		await expect(page.getByText('Paiement indisponible')).toBeVisible({ timeout: 15000 });
	});
});
