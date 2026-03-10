import type { Handle } from '@sveltejs/kit';
import * as Sentry from '@sentry/sveltekit';
import { getTextDirection } from '$lib/paraglide/runtime';
import { paraglideMiddleware } from '$lib/paraglide/server';

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

export const handle: Handle = handleParaglide;

export const handleError = Sentry.handleErrorWithSentry();
