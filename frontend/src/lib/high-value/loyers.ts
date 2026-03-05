import type { Loyer, LoyerCreatePayload, LoyerStatus } from '../api';
import { formatEur } from './formatters';

export type LoyerFormInput = {
	idBien: string;
	idLocataire: string;
	dateLoyer: string;
	montant: string;
	statut: LoyerStatus;
};

export function buildLoyerPayload(input: LoyerFormInput): LoyerCreatePayload | null {
	const idBien = input.idBien.trim();
	const idLocataire = input.idLocataire.trim();
	const numericAmount = Number.parseFloat(input.montant);

	if (!idBien || !input.dateLoyer || !Number.isFinite(numericAmount)) {
		return null;
	}

	const payload: LoyerCreatePayload = {
		id_bien: idBien,
		date_loyer: input.dateLoyer,
		montant: numericAmount,
		statut: input.statut
	};

	if (idLocataire) {
		payload.id_locataire = idLocataire;
	}

	return payload;
}

export function mapLoyerStatusLabel(status: string | null | undefined) {
	const normalized = normalizeLoyerStatus(status);
	if (normalized === 'paye') return 'Payé';
	if (normalized === 'en_retard') return 'En retard';
	if (normalized === 'en_attente') return 'En attente';
	return 'Enregistré';
}

export function mapLoyerStatusClass(status: string | null | undefined) {
	const normalized = normalizeLoyerStatus(status);
	if (normalized === 'paye') return 'bg-emerald-100 text-emerald-800';
	if (normalized === 'en_retard') return 'bg-rose-100 text-rose-800';
	if (normalized === 'en_attente') return 'bg-amber-100 text-amber-800';
	return 'bg-cyan-100 text-cyan-800';
}

export function calculateLoyerMetrics(loyers: Loyer[]) {
	const count = loyers.length;
	const paidLoyers = loyers.filter((loyer) => normalizeLoyerStatus(loyer.statut) === 'paye');
	const lateLoyers = loyers.filter((loyer) => normalizeLoyerStatus(loyer.statut) === 'en_retard');
	const outstandingLoyers = loyers.filter((loyer) => normalizeLoyerStatus(loyer.statut) !== 'paye');
	const totalRecorded = loyers.reduce((sum, loyer) => sum + (loyer.montant ?? 0), 0);
	const totalPaid = paidLoyers.reduce((sum, loyer) => sum + (loyer.montant ?? 0), 0);
	const totalOutstanding = outstandingLoyers.reduce((sum, loyer) => sum + (loyer.montant ?? 0), 0);
	const collectionRate = totalRecorded > 0 ? (totalPaid / totalRecorded) * 100 : 0;

	return {
		count,
		paidCount: paidLoyers.length,
		lateCount: lateLoyers.length,
		totalRecorded,
		totalRecordedLabel: formatEur(totalRecorded),
		totalPaid,
		totalPaidLabel: formatEur(totalPaid),
		totalOutstanding,
		totalOutstandingLabel: formatEur(totalOutstanding),
		averageRecordedLabel: count > 0 ? formatEur(totalRecorded / count) : '—',
		collectionRate,
		collectionRateLabel: count > 0 ? `${Math.round(collectionRate)}%` : '0%'
	};
}

function normalizeLoyerStatus(status: string | null | undefined) {
	if (!status) return 'enregistre';
	if (status.toLowerCase() === 'retard') return 'en_retard';
	return status.toLowerCase();
}
