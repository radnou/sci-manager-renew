import type { Fiscalite } from '$lib/api';
import { formatEur } from '$lib/high-value/formatters';

export function calculateFiscaliteMetrics(exercices: Fiscalite[]) {
	const sorted = [...exercices].sort(
		(left, right) => Number(right.annee || 0) - Number(left.annee || 0)
	);
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
