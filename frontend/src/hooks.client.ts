import * as Sentry from '@sentry/sveltekit';

if (import.meta.env.VITE_SENTRY_DSN) {
	Sentry.init({
		dsn: import.meta.env.VITE_SENTRY_DSN,
		tracesSampleRate: import.meta.env.PROD ? 0.2 : 1.0,
		environment: import.meta.env.MODE
	});
}

export const handleError = Sentry.handleErrorWithSentry();
