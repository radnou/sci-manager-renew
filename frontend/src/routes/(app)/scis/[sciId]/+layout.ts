import type { LayoutLoad } from './$types';
import { error } from '@sveltejs/kit';
import { fetchSciDetail, type SCIDetail } from '$lib/api';

export const load: LayoutLoad = async ({ params, parent }) => {
	const parentData = await parent();

	let sci: SCIDetail;
	try {
		sci = await fetchSciDetail(params.sciId);
	} catch {
		throw error(404, 'SCI non trouvée');
	}

	// Find user's role in this SCI
	const membership = sci.associes?.find(
		(a) => a.user_id === parentData.user.id
	);
	const userRole = membership?.role ?? 'associe';

	return { sci, userRole, sciId: params.sciId };
};
