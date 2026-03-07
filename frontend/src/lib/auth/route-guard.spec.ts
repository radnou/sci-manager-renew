import { describe, expect, it } from 'vitest';

import { buildLoginRedirect, isGuestOnlyRoute, isProtectedRoute } from './route-guard';

describe('route guard helpers', () => {
	it('marks operational routes as protected', () => {
		expect(isProtectedRoute('/dashboard')).toBe(true);
		expect(isProtectedRoute('/scis')).toBe(true);
		expect(isProtectedRoute('/biens/123')).toBe(true);
		expect(isProtectedRoute('/associes')).toBe(true);
		expect(isProtectedRoute('/charges')).toBe(true);
		expect(isProtectedRoute('/fiscalite')).toBe(true);
		expect(isProtectedRoute('/locataires')).toBe(true);
		expect(isProtectedRoute('/loyers')).toBe(true);
		expect(isProtectedRoute('/account/privacy')).toBe(true);
		expect(isProtectedRoute('/settings')).toBe(true);
		expect(isProtectedRoute('/pricing')).toBe(false);
		expect(isProtectedRoute('/')).toBe(false);
	});

	it('marks auth entry routes as guest-only', () => {
		expect(isGuestOnlyRoute('/login')).toBe(true);
		expect(isGuestOnlyRoute('/register')).toBe(true);
		expect(isGuestOnlyRoute('/dashboard')).toBe(false);
	});

	it('builds a login redirect with the original target', () => {
		expect(buildLoginRedirect('/biens', '?tab=portfolio')).toBe(
			'/login?next=%2Fbiens%3Ftab%3Dportfolio'
		);
	});
});
