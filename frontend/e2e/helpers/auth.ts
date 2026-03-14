import type { Page } from '@playwright/test';
import { test } from '@playwright/test';

/**
 * localStorage key used by the app to detect a fake E2E session.
 * See: src/lib/auth/session.ts — parseFakeSession()
 */
const E2E_FAKE_SESSION_KEY = 'gerersci.e2e-fake-session';

/**
 * Returns true when the E2E_AUTH_TOKEN environment variable is set,
 * meaning we can inject a fake Supabase session for authenticated flows.
 */
export function hasAuthToken(): boolean {
	return !!process.env.E2E_AUTH_TOKEN;
}

/**
 * Injects a fake Supabase session into localStorage so the app's
 * `getCurrentSession()` returns a valid session without hitting Supabase Auth.
 *
 * Must be called BEFORE navigating to an auth-gated route.
 *
 * Usage:
 *   await injectFakeSession(page);
 *   await page.goto('/dashboard');
 */
export async function injectFakeSession(page: Page): Promise<void> {
	const token = process.env.E2E_AUTH_TOKEN;
	if (!token) {
		throw new Error(
			'E2E_AUTH_TOKEN is not set. Cannot inject fake session.'
		);
	}

	const userId = process.env.E2E_USER_ID || '00000000-0000-0000-0000-000000000e2e';
	const userEmail = process.env.E2E_USER_EMAIL || 'e2e@gerersci.test';

	const now = Math.floor(Date.now() / 1000);

	const fakeSession = {
		access_token: token,
		refresh_token: 'e2e-fake-refresh-token',
		expires_in: 3600,
		expires_at: now + 3600,
		user: {
			id: userId,
			email: userEmail,
			aud: 'authenticated',
			role: 'authenticated'
		}
	};

	// We need to be on a page from the same origin before setting localStorage.
	// Navigate to a blank page on the same origin first.
	await page.goto('/', { waitUntil: 'commit' });

	await page.evaluate(
		({ key, session }) => {
			window.localStorage.setItem(key, JSON.stringify(session));
		},
		{ key: E2E_FAKE_SESSION_KEY, session: fakeSession }
	);
}

/**
 * Clears the fake session from localStorage.
 */
export async function clearFakeSession(page: Page): Promise<void> {
	await page.evaluate((key) => {
		window.localStorage.removeItem(key);
	}, E2E_FAKE_SESSION_KEY);
}

/**
 * Use inside test.describe() to skip the entire block when
 * E2E_AUTH_TOKEN is not available.
 *
 * Usage:
 *   test.describe('Dashboard', () => {
 *     skipIfNoAuth();
 *     // ... tests that require auth
 *   });
 */
export function skipIfNoAuth(): void {
	test.skip(!hasAuthToken(), 'Skipped: E2E_AUTH_TOKEN not set');
}

/**
 * Standard screenshot directory for all E2E artifacts.
 */
export const SCREENSHOT_DIR = 'e2e-artifacts/screenshots';

/**
 * Takes both a viewport and a full-page screenshot with descriptive names.
 */
export async function takeScreenshots(
	page: Page,
	name: string
): Promise<void> {
	// Short pause for animations and rendering
	await page.waitForTimeout(400);

	await page.screenshot({
		path: `${SCREENSHOT_DIR}/${name}.png`,
		fullPage: false
	});
	await page.screenshot({
		path: `${SCREENSHOT_DIR}/${name}-full.png`,
		fullPage: true
	});
}
