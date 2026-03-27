import { test as base, type Page } from '@playwright/test';

/**
 * Auth fixture for E2E tests.
 *
 * Supports 3 modes:
 * 1. E2E_MAGIC_LINK_URL — visit a magic link
 * 2. E2E_EMAIL + E2E_PASSWORD — login via Supabase REST API + inject session
 * 3. E2E_AUTH_TOKEN — inject JWT directly
 */

export const hasAuth = () =>
	!!process.env.E2E_MAGIC_LINK_URL ||
	(!!process.env.E2E_EMAIL && !!process.env.E2E_PASSWORD) ||
	!!process.env.E2E_AUTH_TOKEN;

export const test = base.extend<{ authedPage: Page }>({
	authedPage: async ({ page, baseURL }, use) => {
		if (!hasAuth()) {
			test.skip();
			return;
		}

		const magicLinkUrl = process.env.E2E_MAGIC_LINK_URL;
		const email = process.env.E2E_EMAIL;
		const password = process.env.E2E_PASSWORD;

		if (magicLinkUrl) {
			await page.goto(magicLinkUrl, { waitUntil: 'networkidle' });
			await page.waitForURL(/gerersci\.fr|localhost/, { timeout: 30_000 });
			await page.waitForLoadState('networkidle');
		} else if (email && password) {
			// Mode 2: Login via Supabase REST API, then inject the session into the browser
			// This works both in local dev and production because we control the session
			const supabaseUrl = process.env.VITE_SUPABASE_URL
				|| (baseURL?.includes('gerersci.fr') ? 'https://api.gerersci.fr' : 'http://127.0.0.1:54321');
			const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY
				|| 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';

			// Get real session from Supabase Auth REST API
			const loginResponse = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=password`, {
				method: 'POST',
				headers: {
					'apikey': supabaseAnonKey,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ email, password })
			});

			if (!loginResponse.ok) {
				const errBody = await loginResponse.text();
				throw new Error(`Supabase login failed (${loginResponse.status}): ${errBody}`);
			}

			const session = await loginResponse.json();
			if (!session.access_token) {
				throw new Error(`No access_token in login response: ${JSON.stringify(session).slice(0, 200)}`);
			}

			// Navigate to app to set correct origin for localStorage
			await page.goto('/login');
			await page.waitForLoadState('domcontentloaded');

			// Determine the Supabase storage key from the URL
			const hostname = new URL(supabaseUrl).hostname;
			const storageKey = `sb-${hostname}-auth-token`;

			// Inject the real session into the Supabase SDK's localStorage
			await page.evaluate(({ storageKey, session }) => {
				// Set overlays dismissed
				localStorage.setItem('gerersci_cookie_consent', 'all');
				localStorage.setItem('gerersci_tour_completed', 'true');
				// Set the Supabase session exactly as the SDK stores it
				const sessionData = {
					access_token: session.access_token,
					refresh_token: session.refresh_token,
					token_type: session.token_type || 'bearer',
					expires_in: session.expires_in,
					expires_at: session.expires_at,
					user: session.user
				};
				localStorage.setItem(storageKey, JSON.stringify(sessionData));
			}, { storageKey, session });

			// Navigate to dashboard — the SDK will pick up the session from localStorage
			await page.goto('/dashboard');
			await page.waitForLoadState('networkidle');
			await page.waitForTimeout(2000);

			// Dismiss any overlays that appeared
			const tour = page.getByRole('button', { name: /Passer/i });
			if (await tour.isVisible({ timeout: 800 }).catch(() => false)) await tour.click();
			const cookie = page.getByRole('button', { name: /Tout accepter/i });
			if (await cookie.isVisible({ timeout: 500 }).catch(() => false)) await cookie.click();
		} else {
			// Mode 3: Token injection (dev/local only)
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
			await page.evaluate((s) => {
				localStorage.setItem('sb-api-auth-token', JSON.stringify(s));
				localStorage.setItem('sb-auth-token', JSON.stringify(s));
				localStorage.setItem('gerersci.e2e-fake-session', JSON.stringify(s));
			}, fakeSession);
			await page.reload();
			await page.waitForLoadState('networkidle');
		}

		await use(page);
	}
});

export { expect } from '@playwright/test';

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
