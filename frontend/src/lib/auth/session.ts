import { browser } from '$app/environment';
import type { Session } from '@supabase/supabase-js';
import { supabase } from '$lib/supabase';

export const E2E_FAKE_SESSION_STORAGE_KEY = 'gerersci.e2e-fake-session';

type SessionSubscription = {
	unsubscribe: () => void;
};

type FakeSessionPayload = {
	access_token?: string;
	refresh_token?: string;
	expires_in?: number;
	expires_at?: number;
	user?: {
		id?: string;
		email?: string;
		aud?: string;
		role?: string;
		[key: string]: unknown;
	};
};

function parseFakeSession(): Session | null {
	if (!browser) {
		return null;
	}

	const raw = window.localStorage.getItem(E2E_FAKE_SESSION_STORAGE_KEY);
	if (!raw) {
		return null;
	}

	try {
		const payload = JSON.parse(raw) as FakeSessionPayload;
		const accessToken = payload.access_token;
		const userId = payload.user?.id;

		if (!accessToken || !userId) {
			return null;
		}

		const now = Math.floor(Date.now() / 1000);
		const expiresIn = payload.expires_in && payload.expires_in > 0 ? payload.expires_in : 3600;
		const expiresAt = payload.expires_at && payload.expires_at > now ? payload.expires_at : now + expiresIn;

		return {
			access_token: accessToken,
			refresh_token: payload.refresh_token || 'e2e-fake-refresh-token',
			token_type: 'bearer',
			expires_in: expiresIn,
			expires_at: expiresAt,
			user: {
				id: userId,
				email: payload.user?.email || 'fake.user@sci.test',
				aud: payload.user?.aud || 'authenticated',
				role: payload.user?.role || 'authenticated',
				...payload.user
			}
		} as Session;
	} catch {
		return null;
	}
}

export async function getCurrentSession(): Promise<Session | null> {
	const fakeSession = parseFakeSession();
	if (fakeSession) {
		return fakeSession;
	}

	const {
		data: { session }
	} = await supabase.auth.getSession();

	return session;
}

export function subscribeToSessionChanges(callback: (session: Session | null) => void): SessionSubscription {
	const fakeSession = parseFakeSession();
	if (fakeSession) {
		callback(fakeSession);

		if (!browser) {
			return { unsubscribe: () => {} };
		}

		const onStorage = (event: StorageEvent) => {
			if (event.key !== E2E_FAKE_SESSION_STORAGE_KEY) {
				return;
			}
			callback(parseFakeSession());
		};

		window.addEventListener('storage', onStorage);
		return {
			unsubscribe: () => {
				window.removeEventListener('storage', onStorage);
			}
		};
	}

	const {
		data: { subscription }
	} = supabase.auth.onAuthStateChange((_event, session) => {
		callback(session ?? null);
	});

	return {
		unsubscribe: () => {
			subscription.unsubscribe();
		}
	};
}

export function clearFakeSession() {
	if (!browser) {
		return;
	}
	window.localStorage.removeItem(E2E_FAKE_SESSION_STORAGE_KEY);
}
