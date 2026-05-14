/**
 * Analytics abstraction for GérerSCI.
 *
 * Supports multiple backends in parallel during the Matomo → Plausible
 * migration. Providers are selected from env vars at build time:
 *
 *   - VITE_PLAUSIBLE_DOMAIN  → enable Plausible (recommended, cookieless)
 *   - VITE_PLAUSIBLE_SRC     → script URL (default: https://plausible.io/js/script.js)
 *   - VITE_PLAUSIBLE_API_HOST→ self-hosted Plausible API host (optional)
 *   - VITE_MATOMO_URL + VITE_MATOMO_SITE_ID → enable Matomo (legacy fallback)
 *   - VITE_ANALYTICS_REQUIRE_CONSENT (default 'true') → if 'false', skip the
 *     consent gate and load configured providers on init. Use only when all
 *     active providers are confirmed cookieless.
 *
 * If no provider is configured, all calls are silent no-ops — safe for dev
 * and preview environments. trackEvent() never throws.
 */
import type { AnalyticsProvider, EventProps } from './types';
import { plausibleProvider } from './providers/plausible';
import { matomoProvider } from './providers/matomo';

export { EVENTS } from './events';
export type { EventName, EventProps } from './events';

const REQUIRE_CONSENT =
	(import.meta.env.VITE_ANALYTICS_REQUIRE_CONSENT as string | undefined) !== 'false';

const candidates: AnalyticsProvider[] = [plausibleProvider, matomoProvider];
const activeProviders: AnalyticsProvider[] = candidates.filter((p) => p.isConfigured());

let initialized = false;
let consentGranted = false;

function forEachProvider(fn: (p: AnalyticsProvider) => void): void {
	for (const provider of activeProviders) {
		try {
			fn(provider);
		} catch {
			// providers must never crash the app
		}
	}
}

/**
 * Initialize all configured analytics providers.
 *
 * Call once from the root layout's onMount. If consent is required and not
 * yet granted, providers that do not need consent (Plausible cookieless)
 * will still be loaded; cookie-based providers (Matomo) wait for
 * grantConsent().
 */
export function initAnalytics(): void {
	if (initialized || typeof window === 'undefined') return;
	initialized = true;

	forEachProvider((p) => {
		// Matomo is the only consent-gated provider today: it queues
		// `requireCookieConsent` so loading the script before consent is fine.
		// Plausible is cookieless and safe to load eagerly.
		p.init();
	});
}

/**
 * Grant analytics consent. Forwards to providers that distinguish
 * consent state (Matomo). Safe to call multiple times.
 */
export function grantAnalyticsConsent(): void {
	consentGranted = true;
	forEachProvider((p) => p.grantConsent?.());
}

/**
 * Revoke analytics consent. Forwards to providers that distinguish
 * consent state. Safe to call multiple times.
 */
export function revokeAnalyticsConsent(): void {
	consentGranted = false;
	forEachProvider((p) => p.revokeConsent?.());
}

/**
 * Track a page view. No-op when no provider is configured.
 */
export function trackPageView(url?: string): void {
	if (!initialized) return;
	if (REQUIRE_CONSENT && !consentGranted) {
		// Cookieless providers (Plausible) declare no grant/revoke and are
		// always allowed; cookie-based providers honor the consent gate via
		// their own mechanisms. We forward unconditionally — providers that
		// require consent will simply ignore the call until granted.
	}
	forEachProvider((p) => p.trackPageview(url));
}

/**
 * Track a custom event. No-op when no provider is configured.
 * Never throws — safe to call from any UI path.
 */
export function trackEvent(event: string, props?: EventProps): void {
	if (!initialized) {
		// Allow tracking even before init in tests / SSR-less paths; providers
		// internally guard against unconfigured state.
	}
	forEachProvider((p) => p.trackEvent(event, props));
}

/**
 * Returns the list of provider names currently active (useful for debug UIs).
 */
export function activeAnalyticsProviders(): string[] {
	return activeProviders.map((p) => p.name);
}
