/**
 * Plausible Analytics provider (cookieless by default).
 *
 * Plausible is GDPR/RGPD/CCPA-compliant out of the box: no cookies, no
 * personal data, no cross-site tracking. The script can therefore be loaded
 * before consent. We still gate it behind consent by default to keep parity
 * with the existing Matomo flow — flip PLAUSIBLE_REQUIRE_CONSENT to false
 * when adopting fully cookieless mode.
 */
import type { AnalyticsProvider, EventProps } from '../types';

const DOMAIN = import.meta.env.VITE_PLAUSIBLE_DOMAIN as string | undefined;
const SCRIPT_SRC =
	(import.meta.env.VITE_PLAUSIBLE_SRC as string | undefined) ||
	'https://plausible.io/js/script.js';
const API_HOST = import.meta.env.VITE_PLAUSIBLE_API_HOST as string | undefined;

declare global {
	interface Window {
		plausible?: {
			(event: string, options?: { props?: EventProps; u?: string; callback?: () => void }): void;
			q?: unknown[];
		};
	}
}

let loaded = false;

function ensureLoaded(): void {
	if (loaded || typeof document === 'undefined') return;
	if (!DOMAIN) return;

	// Plausible recommends a queue stub so calls made before script load are not lost.
	window.plausible =
		window.plausible ||
		function (...args: unknown[]) {
			(window.plausible!.q = window.plausible!.q || []).push(args);
		};

	const script = document.createElement('script');
	script.defer = true;
	script.src = SCRIPT_SRC;
	script.setAttribute('data-domain', DOMAIN);
	if (API_HOST) {
		script.setAttribute('data-api', `${API_HOST.replace(/\/$/, '')}/api/event`);
	}
	document.head.appendChild(script);
	loaded = true;
}

export const plausibleProvider: AnalyticsProvider = {
	name: 'plausible',
	isConfigured(): boolean {
		return Boolean(DOMAIN);
	},
	init(): void {
		ensureLoaded();
	},
	trackPageview(url?: string): void {
		if (!DOMAIN || typeof window === 'undefined') return;
		ensureLoaded();
		try {
			window.plausible?.('pageview', url ? { u: url } : undefined);
		} catch {
			// never crash the app for analytics
		}
	},
	trackEvent(event: string, props?: EventProps): void {
		if (!DOMAIN || typeof window === 'undefined') return;
		ensureLoaded();
		try {
			window.plausible?.(event, props ? { props } : undefined);
		} catch {
			// silent
		}
	}
};
