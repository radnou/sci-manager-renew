import { describe, expect, it } from 'vitest';

import {
	buildLoginRedirect,
	isGuestOnlyRoute,
	isProtectedRoute,
	isPublicRoute
} from './route-guard';

describe('route guard helpers', () => {
	describe('isProtectedRoute', () => {
		it('marks auth-gated routes as protected', () => {
			expect(isProtectedRoute('/account')).toBe(true);
			expect(isProtectedRoute('/account/privacy')).toBe(true);
			expect(isProtectedRoute('/settings')).toBe(true);
			expect(isProtectedRoute('/admin')).toBe(true);
			expect(isProtectedRoute('/admin/users')).toBe(true);
			expect(isProtectedRoute('/onboarding')).toBe(true);
		});

		it('does not mark public routes as protected', () => {
			expect(isProtectedRoute('/')).toBe(false);
			expect(isProtectedRoute('/login')).toBe(false);
			expect(isProtectedRoute('/register')).toBe(false);
			expect(isProtectedRoute('/pricing')).toBe(false);
			expect(isProtectedRoute('/welcome')).toBe(false);
			expect(isProtectedRoute('/forgot-password')).toBe(false);
		});

		it('/success is no longer a protected route', () => {
			expect(isProtectedRoute('/success')).toBe(false);
		});

		it('app routes are protected by (app) layout, not route-guard', () => {
			expect(isProtectedRoute('/dashboard')).toBe(false);
			expect(isProtectedRoute('/scis')).toBe(false);
		});
	});

	describe('isGuestOnlyRoute', () => {
		it('marks login, register, forgot-password as guest-only', () => {
			expect(isGuestOnlyRoute('/login')).toBe(true);
			expect(isGuestOnlyRoute('/register')).toBe(true);
			expect(isGuestOnlyRoute('/forgot-password')).toBe(true);
		});

		it('does not mark other routes as guest-only', () => {
			expect(isGuestOnlyRoute('/')).toBe(false);
			expect(isGuestOnlyRoute('/pricing')).toBe(false);
			expect(isGuestOnlyRoute('/welcome')).toBe(false);
			expect(isGuestOnlyRoute('/reset-password')).toBe(false);
			expect(isGuestOnlyRoute('/dashboard')).toBe(false);
		});
	});

	describe('isPublicRoute', () => {
		it('marks landing page as public', () => {
			expect(isPublicRoute('/')).toBe(true);
		});

		it('marks auth entry pages as public', () => {
			expect(isPublicRoute('/login')).toBe(true);
			expect(isPublicRoute('/register')).toBe(true);
			expect(isPublicRoute('/forgot-password')).toBe(true);
			expect(isPublicRoute('/reset-password')).toBe(true);
		});

		it('marks marketing and post-payment pages as public', () => {
			expect(isPublicRoute('/pricing')).toBe(true);
			expect(isPublicRoute('/welcome')).toBe(true);
		});

		it('marks legal pages as public', () => {
			expect(isPublicRoute('/cgu')).toBe(true);
			expect(isPublicRoute('/confidentialite')).toBe(true);
			expect(isPublicRoute('/mentions-legales')).toBe(true);
			expect(isPublicRoute('/privacy')).toBe(true);
		});

		it('marks auth callback as public', () => {
			expect(isPublicRoute('/auth')).toBe(true);
			expect(isPublicRoute('/auth/callback')).toBe(true);
		});

		it('does not mark app routes as public', () => {
			expect(isPublicRoute('/dashboard')).toBe(false);
			expect(isPublicRoute('/scis')).toBe(false);
			expect(isPublicRoute('/account')).toBe(false);
			expect(isPublicRoute('/settings')).toBe(false);
			expect(isPublicRoute('/admin')).toBe(false);
			expect(isPublicRoute('/onboarding')).toBe(false);
			expect(isPublicRoute('/finances')).toBe(false);
		});

		it('handles sub-paths correctly', () => {
			expect(isPublicRoute('/login/magic-link')).toBe(true);
			expect(isPublicRoute('/pricing/annual')).toBe(true);
			expect(isPublicRoute('/cgu/details')).toBe(true);
		});
	});

	describe('buildLoginRedirect', () => {
		it('builds a login redirect with the original target', () => {
			expect(buildLoginRedirect('/settings', '?tab=notifications')).toBe(
				'/login?next=%2Fsettings%3Ftab%3Dnotifications'
			);
		});

		it('encodes complex paths correctly', () => {
			expect(buildLoginRedirect('/scis/123')).toBe('/login?next=%2Fscis%2F123');
		});
	});
});
