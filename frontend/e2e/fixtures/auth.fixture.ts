import { test as base, type Page } from '@playwright/test';

/**
 * Auth fixture for E2E tests against production.
 *
 * Supports 3 modes (in priority order):
 * 1. E2E_MAGIC_LINK_URL — visit a magic link to authenticate
 * 2. E2E_EMAIL + E2E_PASSWORD — login via the /login page (real Supabase auth)
 * 3. E2E_AUTH_TOKEN — inject JWT into localStorage (dev mode only)
 */

export const hasAuth = () =>
	!!process.env.E2E_MAGIC_LINK_URL ||
	(!!process.env.E2E_EMAIL && !!process.env.E2E_PASSWORD) ||
	!!process.env.E2E_AUTH_TOKEN;

export const test = base.extend<{ authedPage: Page }>({
	authedPage: async ({ page }, use) => {
		if (!hasAuth()) {
			test.skip();
			return;
		}

		const magicLinkUrl = process.env.E2E_MAGIC_LINK_URL;
		const email = process.env.E2E_EMAIL;
		const password = process.env.E2E_PASSWORD;

		if (magicLinkUrl) {
			// Mode 1: Magic link
			await page.goto(magicLinkUrl, { waitUntil: 'networkidle' });
			await page.waitForURL(/gerersci\.fr|app\.gerersci\.fr/, { timeout: 30_000 });
			await page.waitForLoadState('networkidle');
		} else if (email && password) {
			// Mode 2: Real login via /login page (works in production)
			await page.goto('/login');
			await page.waitForLoadState('networkidle');

			// Dismiss cookie banner if present
			const cookieBtn = page.getByRole('button', { name: /Tout accepter/i });
			if (await cookieBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
				await cookieBtn.click();
				await page.waitForTimeout(500);
			}

			// Fill email — target the form input specifically
			const emailInput = page.locator('form input[type="email"], form input[type="text"]').first();
			await emailInput.waitFor({ state: 'visible', timeout: 5000 });
			await emailInput.fill(email);

			// Fill password (login page defaults to password mode)
			const passwordInput = page.locator('form input[type="password"]').first();
			if (await passwordInput.isVisible({ timeout: 2000 }).catch(() => false)) {
				await passwordInput.fill(password);
			}

			// Submit — target the submit button inside the form
			const submitBtn = page.locator('form button[type="submit"]').first();
			await submitBtn.click();

			// Wait for redirect to dashboard or onboarding
			await page.waitForURL(/\/(dashboard|onboarding|scis|finances|exploitation)/, {
				timeout: 15_000
			});
			await page.waitForLoadState('networkidle');

			// Dismiss cookie banner again (new page after redirect)
			const cookieBtn2 = page.getByRole('button', { name: /Tout accepter/i });
			if (await cookieBtn2.isVisible({ timeout: 1000 }).catch(() => false)) {
				await cookieBtn2.click();
				await page.waitForTimeout(300);
			}
		} else {
			// Mode 3: Token injection (dev/local only — won't work in production)
			await page.goto('/');

			const fakeSession = {
				access_token: process.env.E2E_AUTH_TOKEN,
				refresh_token: 'e2e-refresh-token',
				user: {
					id: process.env.E2E_USER_ID || 'e2e-user-id',
					email: process.env.E2E_USER_EMAIL || 'e2e@gerersci.fr',
					role: 'authenticated'
				},
				expires_at: Math.floor(Date.now() / 1000) + 3600
			};

			await page.evaluate((session) => {
				localStorage.setItem('sb-api-auth-token', JSON.stringify(session));
				localStorage.setItem('sb-auth-token', JSON.stringify(session));
				localStorage.setItem('gerersci.e2e-fake-session', JSON.stringify(session));
			}, fakeSession);

			await page.reload();
			await page.waitForLoadState('networkidle');
		}

		await use(page);
	}
});

export { expect } from '@playwright/test';

// Helper: take both viewport and full-page screenshots
export async function captureScreenshots(
	page: Page,
	name: string,
	dir = 'e2e-artifacts/screenshots'
) {
	await page.waitForLoadState('networkidle');
	await page.waitForTimeout(500);
	await page.screenshot({ path: `${dir}/${name}.png`, fullPage: false });
	await page.screenshot({ path: `${dir}/${name}-full.png`, fullPage: true });
}
