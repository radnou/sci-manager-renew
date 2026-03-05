import { describe, expect, it } from 'vitest';
import { calculatePortfolioMetrics, calculateSciScopeMetrics } from './portfolio';

describe('high-value portfolio helpers', () => {
	const scis = [
		{ id: 'sci-1', nom: 'SCI A', statut: 'exploitation' },
		{ id: 'sci-2', nom: 'SCI B', statut: 'configuration' }
	];

	const biens = [
		{
			id: 'bien-1',
			id_sci: 'sci-1',
			adresse: '1 rue Alpha',
			ville: 'Paris',
			code_postal: '75001',
			type_locatif: 'nu',
			loyer_cc: 1000,
			charges: 100,
			tmi: 30
		},
		{
			id: 'bien-2',
			id_sci: 'sci-2',
			adresse: '2 rue Beta',
			ville: 'Lyon',
			code_postal: '69001',
			type_locatif: 'mixte',
			loyer_cc: 900,
			charges: 80,
			tmi: 20
		}
	];

	const loyers = [
		{
			id: 'loyer-1',
			id_bien: 'bien-1',
			id_sci: 'sci-1',
			date_loyer: '2026-03-01',
			montant: 1000,
			statut: 'paye',
			quitus_genere: true
		},
		{
			id: 'loyer-2',
			id_bien: 'bien-2',
			date_loyer: '2026-03-01',
			montant: 900,
			statut: 'en_attente',
			quitus_genere: false
		}
	];

	it('scopes biens and loyers to one SCI', () => {
		const metrics = calculateSciScopeMetrics('sci-1', biens, loyers);

		expect(metrics.biens).toHaveLength(1);
		expect(metrics.loyers).toHaveLength(1);
		expect(metrics.bienMetrics.totalMonthlyRent).toBe(1000);
		expect(metrics.loyerMetrics.totalPaid).toBe(1000);
	});

	it('calculates portfolio level metrics', () => {
		const metrics = calculatePortfolioMetrics(scis, biens, loyers);

		expect(metrics.sciCount).toBe(2);
		expect(metrics.operationalSciCount).toBe(1);
		expect(metrics.setupSciCount).toBe(1);
		expect(metrics.attentionSciCount).toBe(1);
		expect(metrics.bienMetrics.totalMonthlyRent).toBe(1900);
		expect(metrics.loyerMetrics.totalPaid).toBe(1000);
		expect(metrics.loyerMetrics.totalOutstanding).toBe(900);
	});
});
