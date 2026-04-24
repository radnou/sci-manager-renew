import { browser } from '$app/environment';
import type { Session } from '@supabase/supabase-js';
import { supabase } from '$lib/supabase';

// E2E_FAKE_SESSION_STORAGE_KEY is only meaningful in non-production builds.
// In production, this constant is never accessed at runtime (dead code eliminated by bundler).
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
	// In production builds, never parse fake sessions — always return null immediately.
	if (import.meta.env.MODE === 'production') {
		return null;
	}

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
		const expiresAt =
			payload.expires_at && payload.expires_at > now ? payload.expires_at : now + expiresIn;

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

// Track whether the initial session has been resolved at least once.
// WARNING: Do NOT use this as a guard across SPA navigations.
// Each page mount must independently resolve the session.
let initialSessionResolved = false;

export function resetSessionResolution() {
	initialSessionResolved = false;
}

export async function getCurrentSession(): Promise<Session | null> {
	// parseFakeSession() returns null immediately in production.
	const fakeSession = parseFakeSession();
	if (fakeSession) {
		return fakeSession;
	}

	const {
		data: { session }
	} = await supabase.auth.getSession();

	// If session is null and we haven't resolved the initial session yet,
	// Supabase may still be restoring from storage.
	// Wait briefly for INITIAL_SESSION event before giving up.
	if (!session && browser && !initialSessionResolved) {
		return new Promise<Session | null>((resolve) => {
			const timeout = setTimeout(() => {
				sub.unsubscribe();
				initialSessionResolved = true;
				resolve(null);
			}, 4000);

			const {
				data: { subscription: sub }
			} = supabase.auth.onAuthStateChange((event, s) => {
				if (event === 'INITIAL_SESSION' || event === 'SIGNED_IN') {
					clearTimeout(timeout);
					sub.unsubscribe();
					initialSessionResolved = true;
					resolve(s);
				}
			});
		});
	}

	// If we previously had a session but getSession() returned null,
	// Supabase may be mid-token-refresh. Wait briefly before returning null
	// (which would cause a redirect-to-/login flash on SPA navigation).
	if (!session && browser && initialSessionResolved) {
		const retrySession = await new Promise<Session | null>((resolve) => {
			const timeout = setTimeout(() => {
				retrySub.unsubscribe();
				resolve(null);
			}, 1500);

			const {
				data: { subscription: retrySub }
			} = supabase.auth.onAuthStateChange((event, s) => {
				if (event === 'TOKEN_REFRESHED' || event === 'SIGNED_IN') {
					clearTimeout(timeout);
					retrySub.unsubscribe();
					resolve(s);
				}
			});
		});
		if (retrySession) {
			return retrySession;
		}
	}

	if (session) {
		initialSessionResolved = true;
	}

	return session;
}

export function subscribeToSessionChanges(
	callback: (session: Session | null) => void
): SessionSubscription {
	// parseFakeSession() returns null immediately in production — no E2E path taken.
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
	// No-op in production; only active in dev/test mode.
	if (import.meta.env.MODE === 'production') {
		return;
	}

	if (!browser) {
		return;
	}
	window.localStorage.removeItem(E2E_FAKE_SESSION_STORAGE_KEY);
}
