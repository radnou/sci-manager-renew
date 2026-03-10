import { describe, expect, it } from 'vitest';
import {
	buildLoyerPayload,
	buildLoyerUpdatePayload,
	calculateLoyerMetrics,
	mapLoyerStatusClass,
	mapLoyerStatusLabel
} from './loyers';

describe('high-value loyers helpers', () => {
	it('builds payload from valid form inputs', () => {
		const payload = buildLoyerPayload({
			idBien: ' BIEN-001 ',
			idLocataire: ' LOC-001 ',
			dateLoyer: '2026-03-01',
			montant: '1300',
			statut: 'paye'
		});

		expect(payload).toEqual({
			id_bien: 'BIEN-001',
			id_locataire: 'LOC-001',
			date_loyer: '2026-03-01',
			montant: 1300,
			statut: 'paye'
		});
	});

	it('builds update payload from valid form inputs', () => {
		const payload = buildLoyerUpdatePayload({
			idBien: 'BIEN-001',
			idLocataire: 'LOC-001',
			dateLoyer: '2026-04-01',
			montant: '1500',
			statut: 'paye'
		});

		expect(payload).toEqual({
			date_loyer: '2026-04-01',
			montant: 1500,
			statut: 'paye'
		});
	});

	it('returns null for invalid update payload', () => {
		expect(
			buildLoyerUpdatePayload({
				idBien: 'BIEN-001',
				idLocataire: '',
				dateLoyer: '',
				montant: '1200',
				statut: 'paye'
			})
		).toBeNull();

		expect(
			buildLoyerUpdatePayload({
				idBien: 'BIEN-001',
				idLocataire: '',
				dateLoyer: '2026-04-01',
				montant: 'abc',
				statut: 'paye'
			})
		).toBeNull();
	});

	it('returns null when form data is invalid', () => {
		expect(
			buildLoyerPayload({
				idBien: '',
				idLocataire: '',
				dateLoyer: '2026-03-01',
				montant: '1000',
				statut: 'paye'
			})
		).toBeNull();

		expect(
			buildLoyerPayload({
				idBien: 'BIEN-002',
				idLocataire: '',
				dateLoyer: '',
				montant: '1200',
				statut: 'paye'
			})
		).toBeNull();

		expect(
			buildLoyerPayload({
				idBien: 'BIEN-002',
				idLocataire: '',
				dateLoyer: '2026-03-01',
				montant: 'abc',
				statut: 'paye'
			})
		).toBeNull();
	});

	it('maps status labels and classes', () => {
		expect(mapLoyerStatusLabel('paye')).toBe('Payé');
		expect(mapLoyerStatusLabel('en_retard')).toBe('En retard');
		expect(mapLoyerStatusLabel('en_attente')).toBe('En attente');
		expect(mapLoyerStatusLabel('retard')).toBe('En retard');
		expect(mapLoyerStatusLabel(undefined)).toBe('Enregistré');
		expect(mapLoyerStatusClass('paye')).toBe('bg-emerald-100 text-emerald-800');
		expect(mapLoyerStatusClass('en_attente')).toBe('bg-amber-100 text-amber-800');
		expect(mapLoyerStatusClass('en_retard')).toBe('bg-rose-100 text-rose-800');
		expect(mapLoyerStatusClass('autre')).toBe('bg-cyan-100 text-cyan-800');
	});

	it('calculates revenue metrics and late count', () => {
		const metrics = calculateLoyerMetrics([
			{
				id_bien: 'A',
				date_loyer: '2026-03-01',
				montant: 1000,
				statut: 'paye',
				quitus_genere: false
			},
			{
				id_bien: 'B',
				date_loyer: '2026-03-01',
				montant: 800,
				statut: 'en_retard',
				quitus_genere: false
			},
			{
				id_bien: 'C',
				date_loyer: '2026-03-01',
				montant: 1200,
				statut: 'en_attente',
				quitus_genere: false
			}
		]);

		expect(metrics.count).toBe(3);
		expect(metrics.paidCount).toBe(1);
		expect(metrics.totalRecorded).toBe(3000);
		expect(metrics.totalPaid).toBe(1000);
		expect(metrics.totalOutstanding).toBe(2000);
		expect(metrics.totalPaidLabel).toContain('€');
		expect(metrics.averageRecordedLabel).toContain('€');
		expect(metrics.lateCount).toBe(1);
		expect(metrics.collectionRate).toBeCloseTo(33.33, 1);
	});

	it('returns safe defaults for empty dataset', () => {
		const metrics = calculateLoyerMetrics([]);

		expect(metrics.count).toBe(0);
		expect(metrics.totalRecorded).toBe(0);
		expect(metrics.totalPaid).toBe(0);
		expect(metrics.averageRecordedLabel).toBe('—');
		expect(metrics.lateCount).toBe(0);
		expect(metrics.collectionRateLabel).toBe('0%');
	});

	it('builds payload without id_locataire when empty', () => {
		const payload = buildLoyerPayload({
			idBien: 'BIEN-001',
			idLocataire: '',
			dateLoyer: '2026-03-01',
			montant: '1000',
			statut: 'paye'
		});

		expect(payload).not.toBeNull();
		expect(payload!.id_locataire).toBeUndefined();
	});

	it('handles null/undefined montant in metrics with fallback to zero', () => {
		const metrics = calculateLoyerMetrics([
			{
				id_bien: 'A',
				date_loyer: '2026-03-01',
				montant: null as unknown as number,
				statut: 'paye',
				quitus_genere: false
			},
			{
				id_bien: 'B',
				date_loyer: '2026-03-01',
				montant: undefined as unknown as number,
				statut: 'en_retard',
				quitus_genere: false
			}
		]);

		expect(metrics.totalRecorded).toBe(0);
		expect(metrics.totalPaid).toBe(0);
		expect(metrics.totalOutstanding).toBe(0);
		expect(metrics.count).toBe(2);
		expect(metrics.collectionRate).toBe(0);
	});

	it('normalizes "retard" status to "en_retard" in metrics', () => {
		const metrics = calculateLoyerMetrics([
			{
				id_bien: 'A',
				date_loyer: '2026-03-01',
				montant: 500,
				statut: 'retard',
				quitus_genere: false
			}
		]);

		expect(metrics.lateCount).toBe(1);
		expect(metrics.totalOutstanding).toBe(500);
		expect(metrics.paidCount).toBe(0);
	});

	it('handles null/undefined status in metrics as enregistre', () => {
		const metrics = calculateLoyerMetrics([
			{
				id_bien: 'A',
				date_loyer: '2026-03-01',
				montant: 800,
				statut: null as unknown as string,
				quitus_genere: false
			}
		]);

		// null status normalizes to 'enregistre', which is not 'paye'
		expect(metrics.paidCount).toBe(0);
		expect(metrics.totalOutstanding).toBe(800);
		expect(metrics.lateCount).toBe(0);
	});

	it('maps null/undefined status class to default', () => {
		expect(mapLoyerStatusClass(null)).toBe('bg-cyan-100 text-cyan-800');
		expect(mapLoyerStatusClass(undefined)).toBe('bg-cyan-100 text-cyan-800');
	});

	it('maps "retard" status label to "En retard"', () => {
		expect(mapLoyerStatusLabel('retard')).toBe('En retard');
		expect(mapLoyerStatusClass('retard')).toBe('bg-rose-100 text-rose-800');
	});
});
