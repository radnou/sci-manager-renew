/**
 * Auth helper for showcase tests.
 * Re-exports the fake user seeding from the E2E helpers and provides
 * the capture() screenshot utility used across all showcase flows.
 */
import { createHmac } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { test as base, type Page } from '@playwright/test';

// ---------------------------------------------------------------------------
// Auth skip guard
// ---------------------------------------------------------------------------
export const skipIfNoAuth = () => false; // Showcase tests use page.route() mocks, no real auth needed

// ---------------------------------------------------------------------------
// Screenshot helper — viewport + full-page captures with animation delay
// ---------------------------------------------------------------------------
export async function capture(page: Page, name: string) {
	await page.waitForLoadState('networkidle');
	await page.waitForTimeout(800); // Let animations settle
	const dir = 'marketing/screenshots';
	await page.screenshot({ path: `${dir}/${name}.png` });
	await page.screenshot({ path: `${dir}/${name}-full.png`, fullPage: true });
}

// ---------------------------------------------------------------------------
// CORS headers for API mocks
// ---------------------------------------------------------------------------
export const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

// ---------------------------------------------------------------------------
// Fake user context seeding (replicated from tests/e2e/helpers/fake-user.ts)
// ---------------------------------------------------------------------------
const COOKIE_CONSENT_KEY = 'gerersci_cookie_consent';
const ACTIVE_SCI_KEY = 'gerersci.active-sci-id';
const FAKE_SESSION_KEY = 'gerersci.e2e-fake-session';

function encodeBase64Url(input: string) {
	return Buffer.from(input)
		.toString('base64')
		.replace(/=/g, '')
		.replace(/\+/g, '-')
		.replace(/\//g, '_');
}

function readLocalJwtSecret() {
	const candidates = [
		process.env.SUPABASE_JWT_SECRET,
		...[
			resolve(process.cwd(), '../.env.local'),
			resolve(process.cwd(), '../.env'),
			resolve(process.cwd(), '.env.local'),
			resolve(process.cwd(), '.env')
		].map((filepath) => {
			if (!existsSync(filepath)) return null;
			const content = readFileSync(filepath, 'utf8');
			const match = content.match(/^SUPABASE_JWT_SECRET=(.+)$/m);
			return match?.[1]?.trim() || null;
		})
	].filter((value): value is string => Boolean(value));

	return candidates[0] || 'your_supabase_jwt_secret';
}

function signFakeAccessToken(userId: string, email: string) {
	const secret = readLocalJwtSecret();
	const header = encodeBase64Url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
	const now = Math.floor(Date.now() / 1000);
	const payload = encodeBase64Url(
		JSON.stringify({
			sub: userId,
			email,
			role: 'authenticated',
			aud: 'authenticated',
			exp: now + 3600,
			iat: now
		})
	);
	const signature = createHmac('sha256', secret)
		.update(`${header}.${payload}`)
		.digest('base64')
		.replace(/=/g, '')
		.replace(/\+/g, '-')
		.replace(/\//g, '_');

	return `${header}.${payload}.${signature}`;
}

type SeedOptions = {
	sciId?: string;
	userId?: string;
	email?: string;
};

export async function seedShowcaseUser(page: Page, options: SeedOptions = {}) {
	const sciId = options.sciId ?? 'sci-belleville';
	const userId = options.userId ?? 'user-showcase-001';
	const email = options.email ?? 'sophie.moreau@gerersci.fr';
	const accessToken = signFakeAccessToken(userId, email);

	await page.addInitScript(
		({
			cookieConsentKey,
			activeSciKey,
			fakeSessionKey,
			nextSciId,
			nextUserId,
			nextEmail,
			nextAccessToken
		}) => {
			localStorage.setItem(
				cookieConsentKey,
				JSON.stringify({
					necessary: true,
					analytics: false,
					marketing: false,
					timestamp: Date.now()
				})
			);
			localStorage.setItem(activeSciKey, nextSciId);
			localStorage.setItem(
				fakeSessionKey,
				JSON.stringify({
					access_token: nextAccessToken,
					refresh_token: 'showcase-fake-refresh-token',
					token_type: 'bearer',
					expires_in: 3600,
					expires_at: Math.floor(Date.now() / 1000) + 3600,
					user: {
						id: nextUserId,
						email: nextEmail,
						aud: 'authenticated',
						role: 'authenticated'
					}
				})
			);
		},
		{
			cookieConsentKey: COOKIE_CONSENT_KEY,
			activeSciKey: ACTIVE_SCI_KEY,
			fakeSessionKey: FAKE_SESSION_KEY,
			nextSciId: sciId,
			nextUserId: userId,
			nextEmail: email,
			nextAccessToken: accessToken
		}
	);
}

// ---------------------------------------------------------------------------
// Shared subscription mock (Pro plan, onboarding complete)
// ---------------------------------------------------------------------------
export const PRO_SUBSCRIPTION = {
	plan_key: 'pro',
	plan_name: 'Pro',
	status: 'active',
	mode: 'subscription',
	is_active: true,
	entitlements_version: 1,
	max_scis: 10,
	max_biens: 20,
	current_scis: 2,
	current_biens: 4,
	remaining_scis: 8,
	remaining_biens: 16,
	over_limit: false,
	onboarding_completed: true,
	features: {
		multi_sci_enabled: true,
		charges_enabled: true,
		fiscalite_enabled: true,
		quitus_enabled: true,
		cerfa_enabled: true,
		priority_support: true
	}
};

// Re-export test and expect from Playwright
export { test as base_test, expect } from '@playwright/test';
