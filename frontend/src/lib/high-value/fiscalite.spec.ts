import { describe, expect, it } from 'vitest';

import { calculateFiscaliteMetrics, calculerDeficitFoncier, PLAFOND_DEFICIT_FONCIER, totalBilan, postesBilan } from './fiscalite';

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

// ═══════════════════════════════════════════════════════════════════
//  Déficit foncier — CGI art. 156-I-3°
//  Régression du 2026-08-10 : l'ordre d'imputation légal n'était pas
//  respecté, ce qui sous-évaluait le déficit imputable sur le revenu
//  global du montant exact des intérêts d'emprunt.
// ═══════════════════════════════════════════════════════════════════

describe('calculerDeficitFoncier', () => {
	it('impute les intérêts sur les loyers AVANT les autres charges', () => {
		// Cas de la régression. Ordre légal : 20000 - 5000 = 15000, puis
		// 15000 - 25000 = -10000 imputable. L'ancien calcul donnait 5000.
		const r = calculerDeficitFoncier({
			loyersAnnuels: 20_000,
			chargesDeductibles: 25_000,
			interetsEmprunt: 5_000,
			travaux: 0
		});
		expect(r.deficitImputableRevenuGlobal).toBe(10_000);
		expect(r.deficitInteretsReportable).toBe(0);
		expect(r.resultatFoncier).toBe(-10_000);
	});

	it('exclut du revenu global le déficit né des seuls intérêts', () => {
		// Intérêts 15000 > loyers 10000 : les 5000 d'excédent sont
		// reportables sur revenus fonciers, jamais sur le revenu global.
		const r = calculerDeficitFoncier({
			loyersAnnuels: 10_000,
			chargesDeductibles: 0,
			interetsEmprunt: 15_000,
			travaux: 0
		});
		expect(r.deficitImputableRevenuGlobal).toBe(0);
		expect(r.deficitInteretsReportable).toBe(5_000);
		expect(r.resultatFoncier).toBe(-5_000);
	});

	it('plafonne à 10 700 EUR et reporte le surplus', () => {
		const r = calculerDeficitFoncier({
			loyersAnnuels: 10_000,
			chargesDeductibles: 30_000,
			interetsEmprunt: 0,
			travaux: 0
		});
		expect(r.deficitImputableRevenuGlobal).toBe(PLAFOND_DEFICIT_FONCIER);
		expect(r.deficitExcedentaireReportable).toBe(20_000 - PLAFOND_DEFICIT_FONCIER);
	});

	it('combine excédent d intérêts et plafonnement', () => {
		// Intérêts 12000 > loyers 10000 : 2000 reportables intérêts.
		// Autres charges 20000 sur base 0 : 20000 de déficit, plafonné.
		const r = calculerDeficitFoncier({
			loyersAnnuels: 10_000,
			chargesDeductibles: 20_000,
			interetsEmprunt: 12_000,
			travaux: 0
		});
		expect(r.deficitInteretsReportable).toBe(2_000);
		expect(r.deficitImputableRevenuGlobal).toBe(PLAFOND_DEFICIT_FONCIER);
		expect(r.deficitExcedentaireReportable).toBe(20_000 - PLAFOND_DEFICIT_FONCIER);
	});

	it('additionne travaux et charges déductibles', () => {
		const r = calculerDeficitFoncier({
			loyersAnnuels: 10_000,
			chargesDeductibles: 6_000,
			interetsEmprunt: 0,
			travaux: 9_000
		});
		expect(r.deficitImputableRevenuGlobal).toBe(5_000);
	});

	it('ne produit aucun déficit sur un exercice bénéficiaire', () => {
		const r = calculerDeficitFoncier({
			loyersAnnuels: 20_000,
			chargesDeductibles: 3_000,
			interetsEmprunt: 2_000,
			travaux: 1_000
		});
		expect(r.resultatFoncier).toBe(14_000);
		expect(r.deficitImputableRevenuGlobal).toBe(0);
		expect(r.deficitInteretsReportable).toBe(0);
		expect(r.deficitExcedentaireReportable).toBe(0);
	});

	it('traite les entrées absentes ou négatives comme nulles', () => {
		const r = calculerDeficitFoncier({
			loyersAnnuels: -5_000,
			chargesDeductibles: 1_000,
			interetsEmprunt: -100,
			travaux: 0
		});
		expect(r.deficitImputableRevenuGlobal).toBe(1_000);
		expect(r.deficitInteretsReportable).toBe(0);
	});
});

// ═══════════════════════════════════════════════════════════════════
//  Bilan 2065
//  Régression du 2026-08-10 : le total renvoyé par l'API était compté
//  parmi les postes, doublant le bilan affiché.
// ═══════════════════════════════════════════════════════════════════

describe('totalBilan', () => {
	const actif = { immobilisations: 100_000, creances: 5_000, tresorerie: 20_000, total: 125_000 };

	it('retient le total fourni par l API sans additionner les postes', () => {
		expect(totalBilan(actif)).toBe(125_000);
	});

	it('somme les postes quand l API ne fournit pas de total', () => {
		const { total, ...sansTotal } = actif;
		void total;
		expect(totalBilan(sansTotal)).toBe(125_000);
	});

	it('ignore les valeurs non numériques et les nuls', () => {
		expect(totalBilan({ a: 10, b: null, c: 'x', d: undefined, e: NaN })).toBe(10);
	});

	it('renvoie 0 sur une entrée absente', () => {
		expect(totalBilan(null)).toBe(0);
		expect(totalBilan(undefined)).toBe(0);
		expect(totalBilan({})).toBe(0);
	});
});

describe('postesBilan', () => {
	const actif = { immobilisations: 100_000, creances: 5_000, tresorerie: 20_000, total: 125_000 };

	it('exclut la ligne total et trie par montant décroissant', () => {
		const p = postesBilan(actif, { immobilisations: 'Immobilisations' });
		expect(p.map((x) => x.label)).toEqual(['Immobilisations', 'tresorerie', 'creances']);
		expect(p.some((x) => x.label === 'total')).toBe(false);
	});

	it('masque les postes à zéro', () => {
		expect(postesBilan({ a: 0, b: 5 })).toEqual([{ label: 'b', value: 5 }]);
	});

	it('renvoie une liste vide sur une entrée absente', () => {
		expect(postesBilan(null)).toEqual([]);
	});
});
