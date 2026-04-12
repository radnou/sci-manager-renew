import type { LayoutLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { getCurrentSession } from '$lib/auth/session';
import { fetchSubscriptionEntitlements } from '$lib/api';

export const ssr = false;

export const load: LayoutLoad = async ({ url }) => {
	const session = await getCurrentSession();
	if (!session?.user) {
		throw redirect(302, `/login?next=${encodeURIComponent(url.pathname)}`);
	}

	try {
		const subscription = await fetchSubscriptionEntitlements();

		// Paywall bypass for demo users
		if (!subscription.is_active) {
			// Demo mode: redirect to /welcome if not yet seeded
			if (!subscription.demo_seeded && !url.pathname.startsWith('/welcome')) {
				throw redirect(302, '/welcome');
			}
			// If demo_seeded=true, let them through (DemoBanner + LockedAction handle restrictions)
		}

		// Only redirect to onboarding if user has an active subscription (not demo)
		if (
			subscription.is_active &&
			!subscription.onboarding_completed &&
			!url.pathname.startsWith('/onboarding')
		) {
			throw redirect(302, '/onboarding');
		}

		return { user: session.user, subscription };
	} catch (err) {
		// If it's a redirect, rethrow it
		if (err && typeof err === 'object' && 'status' in err) {
			throw err;
		}
		// API error — redirect to welcome for demo flow (if not already there)
		if (!url.pathname.startsWith('/welcome')) {
			throw redirect(302, '/welcome');
		}
		// Fallback: pricing
		throw redirect(302, '/pricing');
	}
};
