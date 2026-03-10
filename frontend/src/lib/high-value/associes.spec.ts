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

	it('handles null/undefined part values with fallback to zero', () => {
		const metrics = calculateAssociateMetrics([
			{ id: 'a1', nom: 'A', part: null as unknown as number, role: 'gerant', is_account_member: true },
			{ id: 'a2', nom: 'B', part: undefined as unknown as number, role: 'associe', is_account_member: false }
		]);

		expect(metrics.totalParts).toBe(0);
		expect(metrics.remainingParts).toBe(100);
	});

	it('handles null/undefined role with fallback to empty string', () => {
		const metrics = calculateAssociateMetrics([
			{ id: 'a1', nom: 'A', part: 50, role: null as unknown as string, is_account_member: false },
			{ id: 'a2', nom: 'B', part: 50, role: undefined as unknown as string, is_account_member: false }
		]);

		expect(metrics.governanceRoles).toBe(0);
	});

	it('detects co_gerant as a governance role', () => {
		const metrics = calculateAssociateMetrics([
			{ id: 'a1', nom: 'A', part: 50, role: 'co_gerant', is_account_member: false }
		]);

		expect(metrics.governanceRoles).toBe(1);
	});

	it('returns safe defaults for empty array', () => {
		const metrics = calculateAssociateMetrics([]);

		expect(metrics.total).toBe(0);
		expect(metrics.totalParts).toBe(0);
		expect(metrics.remainingParts).toBe(100);
		expect(metrics.accountMembers).toBe(0);
		expect(metrics.governanceRoles).toBe(0);
	});
});
