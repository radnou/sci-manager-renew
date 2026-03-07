import type { Charge } from '$lib/api';
import { formatEur } from '$lib/high-value/formatters';

export const CHARGE_TYPE_OPTIONS = [
	{ value: 'assurance', label: 'Assurance' },
	{ value: 'taxe_fonciere', label: 'Taxe foncière' },
	{ value: 'syndic', label: 'Syndic' },
	{ value: 'entretien', label: 'Entretien' },
	{ value: 'travaux', label: 'Travaux' },
	{ value: 'credit', label: 'Crédit' },
	{ value: 'autre', label: 'Autre' }
];

export function calculateChargeMetrics(charges: Charge[]) {
	const total = round(charges.reduce((sum, charge) => sum + Number(charge.montant ?? 0), 0));
	const latestCharge = [...charges].sort((left, right) =>
		String(right.date_paiement || '').localeCompare(String(left.date_paiement || ''))
	)[0];
	return {
		count: charges.length,
		total,
		totalLabel: formatEur(total, '0 €'),
		averageLabel: charges.length ? formatEur(total / charges.length, '0 €') : '—',
		latestChargeDate: latestCharge?.date_paiement || null
	};
}

function round(value: number) {
	return Math.round(value * 100) / 100;
}
