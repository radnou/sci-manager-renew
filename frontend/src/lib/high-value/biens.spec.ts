import { describe, expect, it } from 'vitest';
import {
	buildBienPayload,
	buildBienUpdatePayload,
	calculateBienMetrics,
	mapBienTypeClass,
	mapBienTypeLabel
} from './biens';

describe('high-value biens helpers', () => {
	it('builds payload with normalized fields and parsed values', () => {
		const payload = buildBienPayload({
			idSci: ' sci-1 ',
			adresse: ' 14 rue Saint-Honore ',
			ville: ' Paris ',
			codePostal: '75001',
			typeLocatif: 'nu',
			loyerCC: '1450',
			charges: '120',
			tmi: '30',
			acquisitionDate: '2024-01-15',
			prixAcquisition: '250000'
		});

		expect(payload).toEqual({
			id_sci: 'sci-1',
			adresse: '14 rue Saint-Honore',
			ville: 'Paris',
			code_postal: '75001',
			type_locatif: 'nu',
			loyer_cc: 1450,
			charges: 120,
			tmi: 30,
			acquisition_date: '2024-01-15',
			prix_acquisition: 250000
		});
	});

	it('returns null if required fields are missing', () => {
		const payload = buildBienPayload({
			idSci: '',
			adresse: '   ',
			ville: 'Paris',
			codePostal: '75A01',
			typeLocatif: 'nu',
			loyerCC: '1200',
			charges: '100',
			tmi: '30',
			acquisitionDate: '',
			prixAcquisition: ''
		});

		expect(payload).toBeNull();
	});

	it('maps type labels and classes', () => {
		expect(mapBienTypeLabel('nu')).toBe('Nu');
		expect(mapBienTypeLabel('meuble')).toBe('Meublé');
		expect(mapBienTypeLabel('mixte')).toBe('Mixte');
		expect(mapBienTypeLabel('saisonnier')).toBe('saisonnier');
		expect(mapBienTypeLabel(undefined)).toBe('Non défini');
		expect(mapBienTypeClass('nu')).toBe('bg-emerald-100 text-emerald-800');
		expect(mapBienTypeClass('meuble')).toBe('bg-cyan-100 text-cyan-800');
		expect(mapBienTypeClass('mixte')).toBe('bg-amber-100 text-amber-800');
		expect(mapBienTypeClass('inconnu')).toBe('bg-slate-100 text-slate-700');
	});

	it('builds bien update payload with nullables', () => {
		const payload = buildBienUpdatePayload({
			idSci: 'sci-1',
			adresse: '10 rue Victor Hugo',
			ville: 'Nantes',
			codePostal: '44000',
			typeLocatif: 'mixte',
			loyerCC: '',
			charges: '',
			tmi: '',
			acquisitionDate: '',
			prixAcquisition: ''
		});

		expect(payload).toEqual({
			adresse: '10 rue Victor Hugo',
			ville: 'Nantes',
			code_postal: '44000',
			type_locatif: 'mixte',
			loyer_cc: 0,
			charges: 0,
			tmi: 0,
			acquisition_date: null,
			prix_acquisition: null
		});
	});

	it('calculates portfolio metrics', () => {
		const metrics = calculateBienMetrics([
			{
				id_sci: 'sci-1',
				adresse: 'A',
				ville: 'Paris',
				code_postal: '75001',
				type_locatif: 'nu',
				loyer_cc: 1000,
				charges: 100,
				tmi: 30
			},
			{
				id_sci: 'sci-1',
				adresse: 'B',
				ville: 'Lyon',
				code_postal: '69001',
				type_locatif: 'mixte',
				loyer_cc: 1200,
				charges: 150,
				tmi: 30
			}
		]);

		expect(metrics.count).toBe(2);
		expect(metrics.totalMonthlyRent).toBe(2200);
		expect(metrics.totalMonthlyRentLabel).toContain('€');
		expect(metrics.totalChargesLabel).toContain('€');
		expect(metrics.averageRentLabel).toContain('€');
	});

	it('returns safe defaults when no asset exists', () => {
		const metrics = calculateBienMetrics([]);

		expect(metrics.count).toBe(0);
		expect(metrics.totalMonthlyRent).toBe(0);
		expect(metrics.averageRentLabel).toBe('—');
		expect(metrics.occupancyRateLabel).toBe('N/A');
	});
});
