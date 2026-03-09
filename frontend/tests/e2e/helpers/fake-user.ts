import { createHmac } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import type { Page } from '@playwright/test';

const COOKIE_CONSENT_KEY = 'gerersci_cookie_consent';
const ACTIVE_SCI_KEY = 'gerersci.active-sci-id';
const FAKE_SESSION_KEY = 'gerersci.e2e-fake-session';

type SeedOptions = {
	sciId?: string;
	userId?: string;
	email?: string;
};

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
			if (!existsSync(filepath)) {
				return null;
			}

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

export async function seedFakeUserContext(page: Page, options: SeedOptions = {}) {
	const sciId = options.sciId ?? 'sci-1';
	const userId = options.userId ?? 'user-e2e-001';
	const email = options.email ?? 'fake.user@sci.test';
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
					refresh_token: 'e2e-fake-refresh-token',
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
