import type { Bien, BienCreatePayload, BienType } from '../api';
import { formatEur } from './formatters';

export type BienFormInput = {
	idSci: string;
	adresse: string;
	ville: string;
	codePostal: string;
	typeLocatif: BienType;
	loyerCC: string;
	charges: string;
	tmi: string;
	acquisitionDate: string;
	prixAcquisition: string;
};

export function buildBienPayload(input: BienFormInput): BienCreatePayload | null {
	const idSci = input.idSci.trim();
	const adresse = input.adresse.trim();
	const ville = input.ville.trim();
	const codePostal = input.codePostal.trim();

	if (!idSci || !adresse || !ville || !/^\d{5}$/.test(codePostal)) {
		return null;
	}

	const loyerCC = toNumberOrFallback(input.loyerCC, 0);
	const charges = toNumberOrFallback(input.charges, 0);
	const tmi = toNumberOrFallback(input.tmi, 0);
	const prixAcquisition = toNumberOrUndefined(input.prixAcquisition);

	const payload: BienCreatePayload = {
		id_sci: idSci,
		adresse,
		ville,
		code_postal: codePostal,
		type_locatif: input.typeLocatif,
		loyer_cc: loyerCC,
		charges,
		tmi
	};

	if (input.acquisitionDate.trim()) {
		payload.acquisition_date = input.acquisitionDate;
	}
	if (typeof prixAcquisition === 'number') {
		payload.prix_acquisition = prixAcquisition;
	}

	return payload;
}

export function mapBienTypeLabel(type: string | null | undefined) {
	if (!type) return 'Non défini';
	if (type.toLowerCase() === 'nu') return 'Nu';
	if (type.toLowerCase() === 'meuble') return 'Meublé';
	if (type.toLowerCase() === 'mixte') return 'Mixte';
	return type;
}

export function mapBienTypeClass(type: string | null | undefined) {
	if (!type) return 'bg-slate-100 text-slate-700';
	if (type.toLowerCase() === 'nu') return 'bg-emerald-100 text-emerald-800';
	if (type.toLowerCase() === 'meuble') return 'bg-cyan-100 text-cyan-800';
	if (type.toLowerCase() === 'mixte') return 'bg-amber-100 text-amber-800';
	return 'bg-slate-100 text-slate-700';
}

export function calculateBienMetrics(biens: Bien[]) {
	const totalMonthlyRent = biens.reduce((sum, bien) => sum + (bien.loyer_cc ?? 0), 0);
	const totalCharges = biens.reduce((sum, bien) => sum + (bien.charges ?? 0), 0);
	const count = biens.length;

	return {
		count,
		totalMonthlyRent,
		totalMonthlyRentLabel: formatEur(totalMonthlyRent),
		totalChargesLabel: formatEur(totalCharges),
		averageRentLabel: count > 0 ? formatEur(totalMonthlyRent / count) : '—',
		occupancyRateLabel: count > 0 ? 'N/A' : 'N/A'
	};
}

function toNumberOrFallback(value: string, fallback: number): number {
	const parsed = Number.parseFloat(value);
	return Number.isFinite(parsed) ? parsed : fallback;
}

function toNumberOrUndefined(value: string): number | undefined {
	const parsed = Number.parseFloat(value);
	return Number.isFinite(parsed) ? parsed : undefined;
}
