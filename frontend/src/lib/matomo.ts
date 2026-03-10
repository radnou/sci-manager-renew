/**
 * Matomo Analytics integration (RGPD-compliant)
 *
 * Tracking is only activated after cookie consent.
 * Uses the Matomo JS tracker loaded from the self-hosted instance.
 */

const MATOMO_URL = import.meta.env.VITE_MATOMO_URL as string | undefined;
const MATOMO_SITE_ID = import.meta.env.VITE_MATOMO_SITE_ID as string | undefined;

declare global {
	interface Window {
		_paq?: Array<unknown[]>;
	}
}

let initialized = false;

/**
 * Initialize Matomo tracker. Call once after cookie consent is given.
 */
export function initMatomo(): void {
	if (initialized || !MATOMO_URL || !MATOMO_SITE_ID) return;

	const _paq = (window._paq = window._paq || []);

	// Require consent before tracking (RGPD)
	_paq.push(['requireCookieConsent']);
	_paq.push(['setTrackerUrl', `${MATOMO_URL}/matomo.php`]);
	_paq.push(['setSiteId', MATOMO_SITE_ID]);
	_paq.push(['enableLinkTracking']);

	// Load tracker script
	const script = document.createElement('script');
	script.async = true;
	script.src = `${MATOMO_URL}/matomo.js`;
	document.head.appendChild(script);

	initialized = true;
}

/**
 * Grant cookie consent (call when user accepts analytics cookies)
 */
export function grantMatomoConsent(): void {
	window._paq?.push(['setCookieConsentGiven']);
}

/**
 * Revoke cookie consent
 */
export function revokeMatomoConsent(): void {
	window._paq?.push(['forgetCookieConsentGiven']);
}

/**
 * Track a page view (call on SvelteKit navigation)
 */
export function trackPageView(url?: string): void {
	if (!initialized) return;

	const _paq = window._paq || [];
	if (url) {
		_paq.push(['setCustomUrl', url]);
	}
	_paq.push(['setDocumentTitle', document.title]);
	_paq.push(['trackPageView']);
}
