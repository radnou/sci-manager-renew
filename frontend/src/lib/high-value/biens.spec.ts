import { describe, expect, it } from 'vitest';
import { buildBienPayload, calculateBienMetrics, mapBienStatusClass, mapBienStatusLabel } from './biens';

describe('high-value biens helpers', () => {
	it('builds payload with normalized fields and parsed rent', () => {
		const payload = buildBienPayload({
			adresse: ' 14 rue Saint-Honore ',
			ville: ' Paris ',
			loyerCC: '1450',
			statut: 'occupe'
		});

		expect(payload).toEqual({
			adresse: '14 rue Saint-Honore',
			ville: 'Paris',
			loyer_cc: 1450,
			statut: 'occupe'
		});
	});

	it('returns null if required address is missing', () => {
		const payload = buildBienPayload({
			adresse: '   ',
			ville: 'Paris',
			loyerCC: '1200',
			statut: 'occupe'
		});

		expect(payload).toBeNull();
	});

	it('keeps payload valid when rent is not provided', () => {
		const payload = buildBienPayload({
			adresse: '8 avenue des Tilleuls',
			ville: '',
			loyerCC: '',
			statut: 'vacant'
		});

		expect(payload).toEqual({
			adresse: '8 avenue des Tilleuls',
			ville: undefined,
			statut: 'vacant'
		});
	});

	it('maps status labels and classes', () => {
		expect(mapBienStatusLabel('occupe')).toBe('Occupé');
		expect(mapBienStatusLabel('vacant')).toBe('Vacant');
		expect(mapBienStatusLabel(undefined)).toBe('Non défini');
		expect(mapBienStatusLabel('travaux')).toBe('travaux');
		expect(mapBienStatusClass('occupe')).toBe('bg-emerald-100 text-emerald-800');
		expect(mapBienStatusClass('vacant')).toBe('bg-amber-100 text-amber-800');
		expect(mapBienStatusClass('travaux')).toBe('bg-cyan-100 text-cyan-800');
	});

	it('calculates portfolio metrics', () => {
		const metrics = calculateBienMetrics([
			{ adresse: 'A', loyer_cc: 1000, statut: 'occupe' },
			{ adresse: 'B', loyer_cc: 1200, statut: 'vacant' },
			{ adresse: 'C', loyer_cc: 800, statut: 'occupe' }
		]);

		expect(metrics.count).toBe(3);
		expect(metrics.totalMonthlyRent).toBe(3000);
		expect(metrics.totalMonthlyRentLabel).toContain('€');
		expect(metrics.averageRentLabel).toContain('€');
		expect(metrics.occupancyRateLabel).toBe('67%');
	});

	it('returns safe defaults when no asset exists', () => {
		const metrics = calculateBienMetrics([]);

		expect(metrics.count).toBe(0);
		expect(metrics.totalMonthlyRent).toBe(0);
		expect(metrics.averageRentLabel).toBe('—');
		expect(metrics.occupancyRateLabel).toBe('N/A');
	});
});
