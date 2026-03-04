import type { Loyer, LoyerCreatePayload } from '../api';
import { formatEur } from './formatters';

export type LoyerFormInput = {
	idBien: string;
	dateLoyer: string;
	montant: string;
	statut: string;
};

export function buildLoyerPayload(input: LoyerFormInput): LoyerCreatePayload | null {
	const idBien = input.idBien.trim();
	const numericAmount = Number.parseFloat(input.montant);

	if (!idBien || !input.dateLoyer || !Number.isFinite(numericAmount)) {
		return null;
	}

	return {
		id_bien: idBien,
		date_loyer: input.dateLoyer,
		montant: numericAmount,
		statut: input.statut
	};
}

export function mapLoyerStatusLabel(status: string | null | undefined) {
	const normalized = normalizeLoyerStatus(status);
	if (normalized === 'paye') return 'Payé';
	if (normalized === 'retard') return 'Retard';
	if (normalized === 'en_attente') return 'En attente';
	return 'Enregistré';
}

export function mapLoyerStatusClass(status: string | null | undefined) {
	const normalized = normalizeLoyerStatus(status);
	if (normalized === 'paye') return 'bg-emerald-100 text-emerald-800';
	if (normalized === 'retard') return 'bg-rose-100 text-rose-800';
	if (normalized === 'en_attente') return 'bg-amber-100 text-amber-800';
	return 'bg-cyan-100 text-cyan-800';
}

export function calculateLoyerMetrics(loyers: Loyer[]) {
	const totalCollected = loyers.reduce((sum, loyer) => sum + (loyer.montant ?? 0), 0);
	const count = loyers.length;
	const lateCount = loyers.filter((loyer) => normalizeLoyerStatus(loyer.statut) === 'retard').length;

	return {
		count,
		totalCollected,
		totalCollectedLabel: formatEur(totalCollected),
		averageCollectedLabel: count > 0 ? formatEur(totalCollected / count) : '—',
		lateCount
	};
}

function normalizeLoyerStatus(status: string | null | undefined) {
	if (!status) return 'enregistre';
	return status.toLowerCase();
}
