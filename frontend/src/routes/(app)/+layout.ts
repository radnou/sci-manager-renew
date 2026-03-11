import type { LayoutLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { getCurrentSession } from '$lib/auth/session';
import { fetchSubscriptionEntitlements } from '$lib/api';

export const ssr = false;

export const load: LayoutLoad = async ({ url }) => {
	const session = await getCurrentSession();
	if (!session?.user) {
		throw redirect(302, `/login?redirect=${encodeURIComponent(url.pathname)}`);
	}

	try {
		const subscription = await fetchSubscriptionEntitlements();

		// Paywall: redirect if no active subscription (unless already on pricing-related page)
		if (!subscription.is_active) {
			throw redirect(302, '/pricing');
		}

		// Onboarding: redirect if not completed (unless already on onboarding page)
		if (!subscription.onboarding_completed && !url.pathname.startsWith('/onboarding')) {
			throw redirect(302, '/onboarding');
		}

		return { user: session.user, subscription };
	} catch (err) {
		// If it's a redirect, rethrow it
		if (err && typeof err === 'object' && 'status' in err) {
			throw err;
		}
		// API error (e.g. network) — let user through with minimal data
		return {
			user: session.user,
			subscription: {
				plan_key: 'free' as const,
				plan_name: 'Free',
				status: 'free',
				mode: 'subscription' as const,
				is_active: true,
				entitlements_version: 1,
				current_scis: 0,
				current_biens: 0,
				over_limit: false,
				features: {},
				onboarding_completed: true
			}
		};
	}
};
