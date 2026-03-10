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

	it('scopes loyers by id_bien linkage when loyer has no id_sci', () => {
		const loyerWithoutSci = [
			{
				id: 'loyer-3',
				id_bien: 'bien-1',
				date_loyer: '2026-04-01',
				montant: 500,
				statut: 'paye',
				quitus_genere: false
			}
		];

		const metrics = calculateSciScopeMetrics('sci-1', biens, loyerWithoutSci);
		expect(metrics.loyers).toHaveLength(1);
		expect(metrics.loyers[0].montant).toBe(500);
	});

	it('excludes loyers without id_sci that do not match any scoped bien', () => {
		const loyerWithoutSci = [
			{
				id: 'loyer-4',
				id_bien: 'bien-unknown',
				date_loyer: '2026-04-01',
				montant: 500,
				statut: 'paye',
				quitus_genere: false
			}
		];

		const metrics = calculateSciScopeMetrics('sci-1', biens, loyerWithoutSci);
		expect(metrics.loyers).toHaveLength(0);
	});

	it('handles null/undefined id_sci on biens with fallback', () => {
		const biensNoSci = [
			{
				id: 'bien-x',
				id_sci: null as unknown as string,
				adresse: 'X',
				ville: 'Paris',
				code_postal: '75001',
				type_locatif: 'nu' as const,
				loyer_cc: 500,
				charges: 50,
				tmi: 10
			}
		];

		const metrics = calculateSciScopeMetrics('sci-1', biensNoSci, []);
		expect(metrics.biens).toHaveLength(0);
	});

	it('handles null/undefined statut on SCIs defaulting to configuration', () => {
		const scisNoStatus = [
			{ id: 'sci-a', nom: 'SCI No Status', statut: null as unknown as string },
			{ id: 'sci-b', nom: 'SCI Undefined', statut: undefined as unknown as string }
		];

		const metrics = calculatePortfolioMetrics(scisNoStatus, [], []);

		// null/undefined statut defaults to 'configuration'
		expect(metrics.setupSciCount).toBe(2);
		expect(metrics.operationalSciCount).toBe(0);
		// Both are in configuration and have 0 biens, so they require attention
		expect(metrics.attentionSciCount).toBe(2);
	});

	it('detects mise_en_service as operational status', () => {
		const scisOperational = [
			{ id: 'sci-op', nom: 'SCI Op', statut: 'mise_en_service' }
		];

		const metrics = calculatePortfolioMetrics(scisOperational, [], []);
		expect(metrics.operationalSciCount).toBe(1);
		expect(metrics.setupSciCount).toBe(0);
	});

	it('flags SCI with late loyers as needing attention', () => {
		const scisActive = [
			{ id: 'sci-1', nom: 'SCI A', statut: 'exploitation' }
		];
		const biensActive = [
			{
				id: 'bien-1',
				id_sci: 'sci-1',
				adresse: '1 rue Alpha',
				ville: 'Paris',
				code_postal: '75001',
				type_locatif: 'nu' as const,
				loyer_cc: 1000,
				charges: 100,
				tmi: 30
			}
		];
		const loyersLate = [
			{
				id: 'loyer-late',
				id_bien: 'bien-1',
				id_sci: 'sci-1',
				date_loyer: '2026-01-01',
				montant: 1000,
				statut: 'en_retard',
				quitus_genere: false
			}
		];

		const metrics = calculatePortfolioMetrics(scisActive, biensActive, loyersLate);
		expect(metrics.attentionSciCount).toBe(1);
	});

	it('returns zero counts for empty portfolio', () => {
		const metrics = calculatePortfolioMetrics([], [], []);

		expect(metrics.sciCount).toBe(0);
		expect(metrics.operationalSciCount).toBe(0);
		expect(metrics.setupSciCount).toBe(0);
		expect(metrics.attentionSciCount).toBe(0);
	});

	it('matches loyer to bien when loyer.id_bien and bien.id are null/undefined', () => {
		const biensNullId = [
			{
				id: null as unknown as string,
				id_sci: 'sci-1',
				adresse: 'X',
				ville: 'Paris',
				code_postal: '75001',
				type_locatif: 'nu' as const,
				loyer_cc: 500,
				charges: 50,
				tmi: 10
			}
		];
		const loyersNullBien = [
			{
				id: 'loyer-x',
				id_bien: null as unknown as string,
				date_loyer: '2026-04-01',
				montant: 500,
				statut: 'paye',
				quitus_genere: false
			}
		];

		// loyer has no id_sci, so it falls to id_bien matching
		// String(null) === String(null) => "null" === "null" => true
		const metrics = calculateSciScopeMetrics('sci-1', biensNullId, loyersNullBien);
		expect(metrics.loyers).toHaveLength(1);
	});

	it('counts attention for exploitation SCI with outstanding loyers', () => {
		const scisExploit = [
			{ id: 'sci-x', nom: 'SCI X', statut: 'exploitation' }
		];
		const biensExploit = [
			{
				id: 'bien-x',
				id_sci: 'sci-x',
				adresse: 'X',
				ville: 'Paris',
				code_postal: '75001',
				type_locatif: 'nu' as const,
				loyer_cc: 1000,
				charges: 100,
				tmi: 30
			}
		];
		const loyersOutstanding = [
			{
				id: 'loyer-out',
				id_bien: 'bien-x',
				id_sci: 'sci-x',
				date_loyer: '2026-03-01',
				montant: 1000,
				statut: 'en_attente',
				quitus_genere: false
			}
		];

		const metrics = calculatePortfolioMetrics(scisExploit, biensExploit, loyersOutstanding);
		// exploitation SCI with outstanding loyers needs attention
		expect(metrics.attentionSciCount).toBe(1);
		// statut is 'exploitation', not 'configuration'
		expect(metrics.setupSciCount).toBe(0);
	});
});
