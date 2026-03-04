import { describe, expect, it } from 'vitest';
import {
	buildLoyerPayload,
	calculateLoyerMetrics,
	mapLoyerStatusClass,
	mapLoyerStatusLabel
} from './loyers';

describe('high-value loyers helpers', () => {
	it('builds payload from valid form inputs', () => {
		const payload = buildLoyerPayload({
			idBien: ' BIEN-001 ',
			dateLoyer: '2026-03-01',
			montant: '1300',
			statut: 'paye'
		});

		expect(payload).toEqual({
			id_bien: 'BIEN-001',
			date_loyer: '2026-03-01',
			montant: 1300,
			statut: 'paye'
		});
	});

	it('returns null when form data is invalid', () => {
		expect(
			buildLoyerPayload({
				idBien: '',
				dateLoyer: '2026-03-01',
				montant: '1000',
				statut: 'paye'
			})
		).toBeNull();

		expect(
			buildLoyerPayload({
				idBien: 'BIEN-002',
				dateLoyer: '',
				montant: '1200',
				statut: 'paye'
			})
		).toBeNull();

		expect(
			buildLoyerPayload({
				idBien: 'BIEN-002',
				dateLoyer: '2026-03-01',
				montant: 'abc',
				statut: 'paye'
			})
		).toBeNull();
	});

	it('maps status labels and classes', () => {
		expect(mapLoyerStatusLabel('paye')).toBe('Payé');
		expect(mapLoyerStatusLabel('retard')).toBe('Retard');
		expect(mapLoyerStatusLabel('en_attente')).toBe('En attente');
		expect(mapLoyerStatusLabel(undefined)).toBe('Enregistré');
		expect(mapLoyerStatusClass('paye')).toBe('bg-emerald-100 text-emerald-800');
		expect(mapLoyerStatusClass('en_attente')).toBe('bg-amber-100 text-amber-800');
		expect(mapLoyerStatusClass('retard')).toBe('bg-rose-100 text-rose-800');
		expect(mapLoyerStatusClass('autre')).toBe('bg-cyan-100 text-cyan-800');
	});

	it('calculates revenue metrics and late count', () => {
		const metrics = calculateLoyerMetrics([
			{ id_bien: 'A', date_loyer: '2026-03-01', montant: 1000, statut: 'paye' },
			{ id_bien: 'B', date_loyer: '2026-03-01', montant: 800, statut: 'retard' },
			{ id_bien: 'C', date_loyer: '2026-03-01', montant: 1200, statut: 'en_attente' }
		]);

		expect(metrics.count).toBe(3);
		expect(metrics.totalCollected).toBe(3000);
		expect(metrics.totalCollectedLabel).toContain('€');
		expect(metrics.averageCollectedLabel).toContain('€');
		expect(metrics.lateCount).toBe(1);
	});

	it('returns safe defaults for empty dataset', () => {
		const metrics = calculateLoyerMetrics([]);

		expect(metrics.count).toBe(0);
		expect(metrics.totalCollected).toBe(0);
		expect(metrics.averageCollectedLabel).toBe('—');
		expect(metrics.lateCount).toBe(0);
	});
});
