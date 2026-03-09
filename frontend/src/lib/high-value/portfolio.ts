import type { Bien, EntityId, Loyer, SCIOverview } from '../api';
import { calculateBienMetrics } from './biens';
import { calculateLoyerMetrics } from './loyers';

export function calculateSciScopeMetrics(sciId: EntityId, biens: Bien[], loyers: Loyer[]) {
	const scopedBiens = biens.filter((bien) => String(bien.id_sci || '') === String(sciId));
	const scopedLoyers = loyers.filter((loyer) => {
		if (loyer.id_sci) {
			return String(loyer.id_sci) === String(sciId);
		}

		const linkedBien = scopedBiens.find(
			(bien) => String(bien.id || '') === String(loyer.id_bien || '')
		);
		return Boolean(linkedBien);
	});

	return {
		biens: scopedBiens,
		loyers: scopedLoyers,
		bienMetrics: calculateBienMetrics(scopedBiens),
		loyerMetrics: calculateLoyerMetrics(scopedLoyers)
	};
}

export type PortfolioMetrics = ReturnType<typeof calculatePortfolioMetrics>;
export type SciScopeMetrics = ReturnType<typeof calculateSciScopeMetrics>;

export function calculatePortfolioMetrics(scis: SCIOverview[], biens: Bien[], loyers: Loyer[]) {
	const bienMetrics = calculateBienMetrics(biens);
	const loyerMetrics = calculateLoyerMetrics(loyers);
	const operationalSciCount = scis.filter((sci) => {
		const normalizedStatus = String(sci.statut || 'configuration').toLowerCase();
		return normalizedStatus === 'mise_en_service' || normalizedStatus === 'exploitation';
	}).length;
	const setupSciCount = scis.filter(
		(sci) => String(sci.statut || 'configuration').toLowerCase() === 'configuration'
	).length;
	const attentionSciCount = scis.filter((sci) => {
		const scopedMetrics = calculateSciScopeMetrics(sci.id, biens, loyers);
		return (
			scopedMetrics.biens.length === 0 ||
			scopedMetrics.loyerMetrics.lateCount > 0 ||
			scopedMetrics.loyerMetrics.totalOutstanding > 0 ||
			String(sci.statut || 'configuration').toLowerCase() === 'configuration'
		);
	}).length;

	return {
		sciCount: scis.length,
		operationalSciCount,
		setupSciCount,
		attentionSciCount,
		bienMetrics,
		loyerMetrics
	};
}
