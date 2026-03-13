import type { PageLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { getCurrentSession } from '$lib/auth/session';

export const ssr = false;

export const load: PageLoad = async () => {
	const session = await getCurrentSession();
	if (session?.user) {
		throw redirect(302, '/dashboard');
	}
};
