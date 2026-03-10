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

	it('handles null/undefined annee values in sorting', () => {
		const metrics = calculateFiscaliteMetrics([
			{ id_sci: 'sci-1', annee: null as unknown as number, total_revenus: 10000, total_charges: 3000, resultat_fiscal: 7000 },
			{ id_sci: 'sci-1', annee: undefined as unknown as number, total_revenus: 12000, total_charges: 4000, resultat_fiscal: 8000 }
		]);

		expect(metrics.count).toBe(2);
		// With null annee values, Number(null) = 0 and Number(undefined) = NaN
		expect(metrics.totalResultLabel).toContain('€');
	});

	it('handles null/undefined resultat_fiscal with fallback to zero', () => {
		const metrics = calculateFiscaliteMetrics([
			{ id_sci: 'sci-1', annee: 2025, total_revenus: 10000, total_charges: 3000, resultat_fiscal: null as unknown as number },
			{ id_sci: 'sci-1', annee: 2024, total_revenus: 12000, total_charges: 4000, resultat_fiscal: undefined as unknown as number }
		]);

		expect(metrics.count).toBe(2);
		expect(metrics.latestYear).toBe(2025);
		// latest.resultat_fiscal is null, so formatEur(0, '0 €') is used
		expect(metrics.latestResultLabel).toContain('0');
		// totalResultat sums up via ?? 0, so 0 + 0 = 0
		expect(metrics.totalResultLabel).toContain('0');
	});
});
