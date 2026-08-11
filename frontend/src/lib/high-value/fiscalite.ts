import type { Fiscalite } from '$lib/api';
import { formatEur } from '$lib/high-value/formatters';

export function calculateFiscaliteMetrics(exercices: Fiscalite[]) {
	const sorted = [...exercices].sort((left, right) => Number(right.annee || 0) - Number(left.annee || 0));
	const latest = sorted[0] ?? null;
	const totalResultat = round(
		exercices.reduce((sum, exercice) => sum + Number(exercice.resultat_fiscal ?? 0), 0)
	);

	return {
		count: exercices.length,
		latestYear: latest?.annee ?? null,
		latestResultLabel: latest ? formatEur(latest.resultat_fiscal ?? 0, '0 €') : 'N/A',
		totalResultLabel: formatEur(totalResultat, '0 €')
	};
}

function round(value: number) {
	return Math.round(value * 100) / 100;
}

// ═══════════════════════════════════════════════════════════════════
//  DÉFICIT FONCIER — CGI art. 156-I-3°
//
//  L'ordre d'imputation est imposé par la loi et n'est pas commutatif :
//
//   1. Les intérêts d'emprunt s'imputent D'ABORD sur les loyers bruts.
//      L'excédent éventuel n'est PAS imputable sur le revenu global : il
//      est reportable 10 ans, sur les seuls revenus fonciers.
//   2. Les autres charges s'imputent ensuite sur le solde. Le déficit qui
//      en résulte est imputable sur le revenu global, plafonné à 10 700 €.
//   3. La fraction au-delà du plafond est reportable 10 ans sur les
//      revenus fonciers.
//
//  Le calcul d'origine retranchait les intérêts de la base sans jamais les
//  déduire des loyers, ce qui sous-évaluait le déficit imputable du montant
//  exact des intérêts. Exemple : loyers 20 000, charges 25 000, intérêts
//  5 000 donnait 5 000 au lieu de 10 000.
// ═══════════════════════════════════════════════════════════════════

/** Plafond d'imputation du déficit foncier sur le revenu global (CGI 156-I-3°). */
export const PLAFOND_DEFICIT_FONCIER = 10_700;

export interface DeficitFoncierEntrees {
	loyersAnnuels: number;
	chargesDeductibles: number;
	interetsEmprunt: number;
	travaux: number;
}

export interface DeficitFoncierResultat {
	/** Résultat foncier net, toutes charges confondues. Négatif = déficit. */
	resultatFoncier: number;
	/** Déficit imputable sur le revenu global, plafonné. Valeur positive. */
	deficitImputableRevenuGlobal: number;
	/** Déficit d'origine intérêts, reportable 10 ans sur revenus fonciers. Positif. */
	deficitInteretsReportable: number;
	/** Fraction au-delà du plafond, reportable 10 ans. Positive. */
	deficitExcedentaireReportable: number;
}

/**
 * Calcule le déficit foncier selon l'ordre d'imputation légal.
 *
 * Toutes les valeurs de sortie sont positives sauf `resultatFoncier`, qui
 * garde son signe.
 */
export function calculerDeficitFoncier(e: DeficitFoncierEntrees): DeficitFoncierResultat {
	const loyers = Math.max(0, e.loyersAnnuels || 0);
	const interets = Math.max(0, e.interetsEmprunt || 0);
	const autresCharges = Math.max(0, (e.chargesDeductibles || 0) + (e.travaux || 0));

	const resultatFoncier = loyers - interets - autresCharges;

	// 1. Intérêts sur loyers bruts. L'excédent ne quitte pas la sphère foncière.
	const soldeApresInterets = loyers - interets;
	const deficitInteretsReportable = soldeApresInterets < 0 ? -soldeApresInterets : 0;
	const baseAutresCharges = Math.max(0, soldeApresInterets);

	// 2. Autres charges sur le solde. Ce déficit-là est imputable.
	const deficitAutresCharges = Math.max(0, autresCharges - baseAutresCharges);

	// 3. Plafonnement, le surplus est reportable.
	const deficitImputableRevenuGlobal = Math.min(deficitAutresCharges, PLAFOND_DEFICIT_FONCIER);
	const deficitExcedentaireReportable = deficitAutresCharges - deficitImputableRevenuGlobal;

	return {
		resultatFoncier,
		deficitImputableRevenuGlobal,
		deficitInteretsReportable,
		deficitExcedentaireReportable
	};
}

// ═══════════════════════════════════════════════════════════════════
//  BILAN 2065
//
//  Le backend renvoie le total DANS le dictionnaire du bilan
//  (backend/app/api/v1/declarations.py : actif={... "total": ...}).
//  Sommer `Object.values` comptait donc les composants ET leur total :
//  le montant affiché valait environ le double du bilan réel.
// ═══════════════════════════════════════════════════════════════════

/** Clé réservée au total dans les dictionnaires de bilan renvoyés par l'API. */
export const CLE_TOTAL_BILAN = 'total';

/**
 * Total d'un côté du bilan, en excluant la clé `total` renvoyée par l'API.
 *
 * Si l'API fournit un total, il fait foi : c'est lui que la liasse doit
 * porter. Sinon on somme les postes.
 */
export function totalBilan(bilan: Record<string, unknown> | null | undefined): number {
	if (!bilan) return 0;

	const fourni = bilan[CLE_TOTAL_BILAN];
	if (typeof fourni === 'number' && Number.isFinite(fourni)) return fourni;

	return Object.entries(bilan)
		.filter(([cle, v]) => cle !== CLE_TOTAL_BILAN && typeof v === 'number' && Number.isFinite(v))
		.reduce((somme, [, v]) => somme + (v as number), 0);
}

/** Postes d'un bilan, hors clé `total`, triés par montant décroissant. */
export function postesBilan(
	bilan: Record<string, unknown> | null | undefined,
	libelles: Record<string, string> = {}
): { label: string; value: number }[] {
	if (!bilan) return [];
	return Object.entries(bilan)
		.filter(
			([cle, v]) =>
				cle !== CLE_TOTAL_BILAN && typeof v === 'number' && Number.isFinite(v) && v !== 0
		)
		.map(([cle, v]) => ({ label: libelles[cle] ?? cle, value: v as number }))
		.sort((a, b) => b.value - a.value);
}
