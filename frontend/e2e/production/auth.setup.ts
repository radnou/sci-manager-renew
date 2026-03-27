import { test as setup, expect } from '@playwright/test';

const AUTH_FILE = 'e2e-artifacts/.auth/session.json';

/**
 * Global setup: login once, save session state for all tests to reuse.
 * This avoids the session-loss problem when page.goto() creates a new context.
 */
setup('authenticate', async ({ page }) => {
	const email = process.env.E2E_EMAIL;
	const password = process.env.E2E_PASSWORD;
	const baseURL = process.env.E2E_BASE_URL || 'http://localhost:5174';
	const supabaseUrl = process.env.VITE_SUPABASE_URL || 'http://127.0.0.1:54321';
	const supabaseAnonKey =
		process.env.VITE_SUPABASE_ANON_KEY ||
		'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';

	if (!email || !password) {
		throw new Error('E2E_EMAIL and E2E_PASSWORD are required for auth setup');
	}

	// 1. Get real session from Supabase REST API
	const loginResponse = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=password`, {
		method: 'POST',
		headers: { apikey: supabaseAnonKey, 'Content-Type': 'application/json' },
		body: JSON.stringify({ email, password })
	});

	if (!loginResponse.ok) {
		throw new Error(`Login failed: ${await loginResponse.text()}`);
	}

	const session = await loginResponse.json();
	expect(session.access_token).toBeTruthy();

	// 2. Navigate to app and inject session + dismiss overlays
	await page.goto(`${baseURL}/login`);
	await page.waitForLoadState('domcontentloaded');

	const hostname = new URL(supabaseUrl).hostname;
	const storageKey = `sb-${hostname}-auth-token`;

	await page.evaluate(
		({ storageKey, session }) => {
			localStorage.setItem('gerersci_cookie_consent', 'all');
			localStorage.setItem('gerersci_tour_completed', 'true');
			localStorage.setItem(
				storageKey,
				JSON.stringify({
					access_token: session.access_token,
					refresh_token: session.refresh_token,
					token_type: session.token_type || 'bearer',
					expires_in: session.expires_in,
					expires_at: session.expires_at,
					user: session.user
				})
			);
		},
		{ storageKey, session }
	);

	// 3. Verify localStorage was set
	const hasSession = await page.evaluate(({ storageKey }) => {
		return !!localStorage.getItem(storageKey);
	}, { storageKey });
	expect(hasSession).toBe(true);

	// 4. Save storage state (includes localStorage)
	await page.context().storageState({ path: AUTH_FILE });

	// Verify the file was written
	const fs = await import('fs');
	expect(fs.existsSync(AUTH_FILE)).toBe(true);
});
