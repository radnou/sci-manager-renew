import { describe, expect, it } from 'vitest';

import { CHARGE_TYPE_OPTIONS, calculateChargeMetrics } from './charges';

describe('high-value charges helpers', () => {
	it('exposes the supported charge types', () => {
		expect(CHARGE_TYPE_OPTIONS.map((option) => option.value)).toEqual([
			'assurance',
			'taxe_fonciere',
			'syndic',
			'entretien',
			'travaux',
			'credit',
			'autre'
		]);
	});

	it('calculates totals and latest movement metadata', () => {
		const metrics = calculateChargeMetrics([
			{ id_bien: 'bien-1', type_charge: 'assurance', montant: 240, date_paiement: '2026-02-10' },
			{ id_bien: 'bien-2', type_charge: 'travaux', montant: 600, date_paiement: '2026-03-02' }
		]);

		expect(metrics.count).toBe(2);
		expect(metrics.total).toBe(840);
		expect(metrics.totalLabel).toContain('€');
		expect(metrics.averageLabel).toContain('€');
		expect(metrics.latestChargeDate).toBe('2026-03-02');
	});

	it('returns safe defaults when no charge exists', () => {
		const metrics = calculateChargeMetrics([]);

		expect(metrics.count).toBe(0);
		expect(metrics.total).toBe(0);
		expect(metrics.averageLabel).toBe('—');
		expect(metrics.latestChargeDate).toBeNull();
	});
});
