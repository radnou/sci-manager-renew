import { describe, expect, it } from 'vitest';

import { ASSOCIE_ROLE_OPTIONS, calculateAssociateMetrics } from './associes';

describe('high-value associes helpers', () => {
	it('exposes the governance role options used by the workspace', () => {
		expect(ASSOCIE_ROLE_OPTIONS.map((option) => option.value)).toEqual([
			'gerant',
			'co_gerant',
			'associe',
			'usufruitier'
		]);
	});

	it('calculates governance metrics from the associate register', () => {
		const metrics = calculateAssociateMetrics([
			{ id: 'associe-1', nom: 'Rad', part: 60, role: 'gerant', is_account_member: true },
			{ id: 'associe-2', nom: 'Camille', part: 39.5, role: 'associe', is_account_member: false }
		]);

		expect(metrics.total).toBe(2);
		expect(metrics.totalParts).toBe(99.5);
		expect(metrics.remainingParts).toBe(0.5);
		expect(metrics.accountMembers).toBe(1);
		expect(metrics.governanceRoles).toBe(1);
	});
});
