import { redirect } from '@sveltejs/kit';
import { getCurrentSession } from '$lib/auth/session';

export const ssr = false;

export async function load() {
	const session = await getCurrentSession();
	if (!session?.user) {
		throw redirect(302, '/login');
	}
	return { user: session.user };
}
