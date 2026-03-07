import { describe, expect, it } from 'vitest';

import { calculateFiscaliteMetrics } from './fiscalite';

describe('high-value fiscalite helpers', () => {
	it('calculates latest exercise and cumulative result', () => {
		const metrics = calculateFiscaliteMetrics([
			{ id_sci: 'sci-1', annee: 2024, total_revenus: 20000, total_charges: 5000, resultat_fiscal: 15000 },
			{ id_sci: 'sci-1', annee: 2025, total_revenus: 24000, total_charges: 6000, resultat_fiscal: 18000 }
		]);

		expect(metrics.count).toBe(2);
		expect(metrics.latestYear).toBe(2025);
		expect(metrics.latestResultLabel).toContain('€');
		expect(metrics.totalResultLabel).toContain('€');
	});

	it('returns a readable fallback when no exercise exists', () => {
		const metrics = calculateFiscaliteMetrics([]);

		expect(metrics.count).toBe(0);
		expect(metrics.latestYear).toBeNull();
		expect(metrics.latestResultLabel).toBe('N/A');
		expect(metrics.totalResultLabel).toContain('0');
	});
});
