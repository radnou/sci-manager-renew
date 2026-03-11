import { describe, expect, it } from 'vitest';

import { buildLoginRedirect, isGuestOnlyRoute, isProtectedRoute } from './route-guard';

describe('route guard helpers', () => {
	it('marks operational routes as protected', () => {
		// These routes are protected by the route-guard (outside (app) layout)
		expect(isProtectedRoute('/account')).toBe(true);
		expect(isProtectedRoute('/account/privacy')).toBe(true);
		expect(isProtectedRoute('/settings')).toBe(true);
		expect(isProtectedRoute('/admin')).toBe(true);
		expect(isProtectedRoute('/onboarding')).toBe(true);
		expect(isProtectedRoute('/success')).toBe(true);
		// Public routes
		expect(isProtectedRoute('/pricing')).toBe(false);
		expect(isProtectedRoute('/')).toBe(false);
		expect(isProtectedRoute('/login')).toBe(false);
		// App routes are protected by (app) layout, not route-guard
		expect(isProtectedRoute('/dashboard')).toBe(false);
		expect(isProtectedRoute('/scis')).toBe(false);
	});

	it('marks auth entry routes as guest-only', () => {
		expect(isGuestOnlyRoute('/login')).toBe(true);
		expect(isGuestOnlyRoute('/register')).toBe(true);
		expect(isGuestOnlyRoute('/dashboard')).toBe(false);
	});

	it('builds a login redirect with the original target', () => {
		expect(buildLoginRedirect('/settings', '?tab=notifications')).toBe(
			'/login?next=%2Fsettings%3Ftab%3Dnotifications'
		);
	});
});
