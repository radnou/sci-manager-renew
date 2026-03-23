import { redirect, type Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';
import * as Sentry from '@sentry/sveltekit';
import { getTextDirection } from '$lib/paraglide/runtime';
import { paraglideMiddleware } from '$lib/paraglide/server';
import { isProtectedRoute, isGuestOnlyRoute } from '$lib/auth/route-guard';

const SENTRY_DSN = process.env.SENTRY_DSN || process.env.VITE_SENTRY_DSN;
if (SENTRY_DSN) {
	Sentry.init({
		dsn: SENTRY_DSN,
		tracesSampleRate: 0.2,
		environment: process.env.NODE_ENV || 'production'
	});
}

const handleParaglide: Handle = ({ event, resolve }) =>
	paraglideMiddleware(event.request, ({ request, locale }) => {
		event.request = request;

		return resolve(event, {
			transformPageChunk: ({ html }) =>
				html
					.replace('%paraglide.lang%', locale)
					.replace('%paraglide.dir%', getTextDirection(locale))
		});
	});

/**
 * Server-side route guard.
 *
 * Supabase JS v2 (without @supabase/ssr) stores sessions in localStorage,
 * but it can also persist a session cookie named `sb-<ref>-auth-token`.
 * We use the presence of any `sb-` prefixed cookie as a lightweight
 * indicator that the user has an active session on this browser.
 *
 * For full cryptographic validation on the server, migrate to @supabase/ssr.
 * This guard provides defence-in-depth against casual unauthenticated access.
 */
const handleAuthGuard: Handle = ({ event, resolve }) => {
	const { pathname } = event.url;

	// In dev/test mode, skip server-side route guard entirely.
	// Client-side guards still apply. This allows E2E tests with mocked auth.
	if (process.env.NODE_ENV !== 'production') {
		return resolve(event);
	}

	// Detect whether a Supabase auth cookie is present.
	const cookieHeader = event.request.headers.get('cookie') ?? '';
	const hasSupabaseCookie = cookieHeader.split(';').some((c) => c.trim().startsWith('sb-'));

	if (isProtectedRoute(pathname) && !hasSupabaseCookie) {
		// Unauthenticated user trying to access a protected page → send to /login.
		const next = encodeURIComponent(pathname + event.url.search);
		redirect(302, `/login?next=${next}`);
	}

	if (isGuestOnlyRoute(pathname) && hasSupabaseCookie) {
		// Already-authenticated user hitting login/register → send to /account.
		redirect(302, '/account');
	}

	return resolve(event);
};

export const handle: Handle = sequence(handleAuthGuard, handleParaglide);

export const handleError = Sentry.handleErrorWithSentry();
