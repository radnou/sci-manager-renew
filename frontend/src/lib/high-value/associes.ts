import type { Associe } from '$lib/api';

export const ASSOCIE_ROLE_OPTIONS = [
	{ value: 'gerant', label: 'Gérant' },
	{ value: 'co_gerant', label: 'Co-gérant' },
	{ value: 'associe', label: 'Associé' },
	{ value: 'usufruitier', label: 'Usufruitier' }
];

export function calculateAssociateMetrics(associes: Associe[]) {
	const total = associes.length;
	const totalParts = round(
		associes.reduce((sum, associe) => sum + Number(associe.part ?? 0), 0)
	);
	const accountMembers = associes.filter((associe) => Boolean(associe.is_account_member)).length;
	const governanceRoles = associes.filter((associe) =>
		String(associe.role || '').toLowerCase().includes('gerant')
	).length;

	return {
		total,
		totalParts,
		remainingParts: round(Math.max(100 - totalParts, 0)),
		accountMembers,
		governanceRoles
	};
}

function round(value: number) {
	return Math.round(value * 100) / 100;
}
