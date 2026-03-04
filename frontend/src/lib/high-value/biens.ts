import type { Bien, BienCreatePayload } from '../api';
import { formatEur } from './formatters';

export type BienFormInput = {
	adresse: string;
	ville: string;
	loyerCC: string;
	statut: string;
};

export function buildBienPayload(input: BienFormInput): BienCreatePayload | null {
	const adresse = input.adresse.trim();
	if (!adresse) {
		return null;
	}

	const basePayload: BienCreatePayload = {
		adresse,
		ville: input.ville.trim() || undefined,
		statut: input.statut
	};

	const parsedLoyer = Number.parseFloat(input.loyerCC);
	if (!input.loyerCC.trim() || !Number.isFinite(parsedLoyer)) {
		return basePayload;
	}

	return {
		...basePayload,
		loyer_cc: parsedLoyer
	};
}

export function mapBienStatusLabel(status: string | null | undefined) {
	if (!status) return 'Non défini';
	if (status.toLowerCase() === 'occupe') return 'Occupé';
	if (status.toLowerCase() === 'vacant') return 'Vacant';
	return status;
}

export function mapBienStatusClass(status: string | null | undefined) {
	if (!status) return 'bg-slate-100 text-slate-700';
	if (status.toLowerCase() === 'occupe') return 'bg-emerald-100 text-emerald-800';
	if (status.toLowerCase() === 'vacant') return 'bg-amber-100 text-amber-800';
	return 'bg-cyan-100 text-cyan-800';
}

export function calculateBienMetrics(biens: Bien[]) {
	const totalMonthlyRent = biens.reduce((sum, bien) => sum + (bien.loyer_cc ?? 0), 0);
	const occupiedCount = biens.filter((bien) => (bien.statut ?? '').toLowerCase() === 'occupe').length;
	const count = biens.length;

	return {
		count,
		totalMonthlyRent,
		totalMonthlyRentLabel: formatEur(totalMonthlyRent),
		averageRentLabel: count > 0 ? formatEur(totalMonthlyRent / count) : '—',
		occupancyRateLabel: count > 0 ? `${Math.round((occupiedCount / count) * 100)}%` : 'N/A'
	};
}
