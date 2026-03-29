export const PLANS = {
	starter: {
		key: 'starter',
		name: 'Gestion',
		description: 'Automatisez votre gestion locative',
		monthlyPrice: 19,
		yearlyPrice: 190,
		popular: false,
		features: [
			'1 SCI',
			'5 biens',
			'Quittances PDF conformes',
			'Suivi des loyers + relances auto',
			'Résumé fiscal CERFA 2044',
			'Charges, PNO, frais agence',
			'Export CSV',
			'Support email 48h',
		],
		cta: 'Démarrer pour 19€/mois',
	},
	pro: {
		key: 'pro',
		name: 'Pilotage',
		description: 'Votre co-pilote fiscal et juridique',
		monthlyPrice: 39,
		yearlyPrice: 390,
		popular: true,
		features: [
			'SCI illimitées',
			'Biens illimités',
			'Tout Gestion inclus',
			'Assemblées générales + convocations',
			'Mouvements de parts + simulation droits',
			'Moteur 44+ échéances',
			'Calendrier fiscal interactif',
			'Vue comptable annuelle',
			'Révision IRL automatique',
			'Support prioritaire 24h',
		],
		cta: 'Démarrer pour 39€/mois',
	},
} as const;

export type PlanKey = keyof typeof PLANS;

export function formatPrice(plan: (typeof PLANS)[PlanKey], period: 'month' | 'year'): string {
	return period === 'month' ? `${plan.monthlyPrice}€` : `${plan.yearlyPrice}€`;
}

export function formatPriceTTC(
	plan: (typeof PLANS)[PlanKey],
	period: 'month' | 'year',
): string {
	const ht = period === 'month' ? plan.monthlyPrice : plan.yearlyPrice;
	const ttc = (ht * 1.2).toFixed(2).replace('.', ',');
	const periodLabel = period === 'month' ? '/mois' : '/an';
	return `(${ttc}€ TTC${periodLabel})`;
}
