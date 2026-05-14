/**
 * Matomo provider — kept as optional legacy fallback during the Plausible
 * migration. Activated only when VITE_MATOMO_URL and VITE_MATOMO_SITE_ID
 * are both set.
 *
 * Tracking respects RGPD: cookies require explicit consent (handled by
 * CookieConsent.svelte through grantConsent / revokeConsent).
 */
import type { AnalyticsProvider, EventProps } from '../types';

const MATOMO_URL = import.meta.env.VITE_MATOMO_URL as string | undefined;
const MATOMO_SITE_ID = import.meta.env.VITE_MATOMO_SITE_ID as string | undefined;

declare global {
	interface Window {
		_paq?: Array<unknown[]>;
	}
}

let initialized = false;

export const matomoProvider: AnalyticsProvider = {
	name: 'matomo',
	isConfigured(): boolean {
		return Boolean(MATOMO_URL && MATOMO_SITE_ID);
	},
	init(): void {
		if (initialized || typeof window === 'undefined') return;
		if (!MATOMO_URL || !MATOMO_SITE_ID) return;

		const _paq = (window._paq = window._paq || []);
		_paq.push(['requireCookieConsent']);
		_paq.push(['setTrackerUrl', `${MATOMO_URL.replace(/\/$/, '')}/matomo.php`]);
		_paq.push(['setSiteId', MATOMO_SITE_ID]);
		_paq.push(['enableLinkTracking']);

		const script = document.createElement('script');
		script.async = true;
		script.src = `${MATOMO_URL.replace(/\/$/, '')}/matomo.js`;
		document.head.appendChild(script);

		initialized = true;
	},
	grantConsent(): void {
		try {
			window._paq?.push(['setCookieConsentGiven']);
		} catch {
			// silent
		}
	},
	revokeConsent(): void {
		try {
			window._paq?.push(['forgetCookieConsentGiven']);
		} catch {
			// silent
		}
	},
	trackPageview(url?: string): void {
		if (!initialized || typeof window === 'undefined') return;
		try {
			const _paq = window._paq || [];
			if (url) _paq.push(['setCustomUrl', url]);
			_paq.push(['setDocumentTitle', document.title]);
			_paq.push(['trackPageView']);
		} catch {
			// silent
		}
	},
	trackEvent(event: string, props?: EventProps): void {
		if (!initialized || typeof window === 'undefined') return;
		try {
			const _paq = window._paq || [];
			// Matomo trackEvent signature: [category, action, name, value]
			// We collapse to category='app' / action=event / name=stringified props.
			const name = props ? JSON.stringify(props) : undefined;
			_paq.push(['trackEvent', 'app', event, name]);
		} catch {
			// silent
		}
	}
};
