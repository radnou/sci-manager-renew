import type { Page } from '@playwright/test';

const COOKIE_CONSENT_KEY = 'sci_manager_cookie_consent';
const ACTIVE_SCI_KEY = 'sci-manager.active-sci-id';
const FAKE_SESSION_KEY = 'sci-manager.e2e-fake-session';

type SeedOptions = {
	sciId?: string;
	userId?: string;
	email?: string;
};

export async function seedFakeUserContext(page: Page, options: SeedOptions = {}) {
	const sciId = options.sciId ?? 'sci-1';
	const userId = options.userId ?? 'user-e2e-001';
	const email = options.email ?? 'fake.user@sci.test';

	await page.addInitScript(
		({
			cookieConsentKey,
			activeSciKey,
			fakeSessionKey,
			nextSciId,
			nextUserId,
			nextEmail
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
					access_token: 'e2e-fake-access-token',
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
			nextEmail: email
		}
	);
}
