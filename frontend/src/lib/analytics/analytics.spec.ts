import { describe, it, expect } from 'vitest';
import { EVENTS, trackEvent, trackPageView, activeAnalyticsProviders } from './index';

describe('analytics surface', () => {
	it('exposes the canonical EVENTS map', () => {
		expect(EVENTS.LOGIN_START).toBe('login_start');
		expect(EVENTS.PRICING_PLAN_SELECT).toBe('pricing_plan_select');
		expect(EVENTS.DEMO_LOCKED_ACTION).toBe('demo_locked_action');
	});

	it('trackEvent never throws when no provider is configured', () => {
		// In test env none of VITE_PLAUSIBLE_DOMAIN / VITE_MATOMO_URL are set,
		// so activeAnalyticsProviders() is empty and every call is a no-op.
		expect(activeAnalyticsProviders()).toEqual([]);
		expect(() => trackEvent('test_event', { foo: 'bar' })).not.toThrow();
		expect(() => trackPageView('/some/path')).not.toThrow();
	});
});
