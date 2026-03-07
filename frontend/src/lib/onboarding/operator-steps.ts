export type OperatorOnboardingScope = 'all' | 'portfolio' | 'exploitation' | 'finance';

export type OperatorOnboardingMetrics = {
	sciCount: number;
	associeCount: number;
	bienCount: number;
	locataireCount: number;
	loyerCount: number;
	chargeCount: number;
	fiscaliteCount: number;
	activeSciLabel?: string;
};

export type OperatorOnboardingStep = {
	key: string;
	title: string;
	description: string;
	href: string;
	actionLabel: string;
	done: boolean;
	group: Exclude<OperatorOnboardingScope, 'all'>;
};

export function buildOperatorOnboardingSteps(
	metrics: OperatorOnboardingMetrics,
	scope: OperatorOnboardingScope = 'all'
): OperatorOnboardingStep[] {
	const steps: OperatorOnboardingStep[] = [
		{
			key: 'sci',
			title: metrics.sciCount > 0 ? 'Portefeuille SCI en place' : 'Créer ou sélectionner la SCI',
			description:
				metrics.sciCount > 0
					? `${metrics.sciCount} SCI disponible(s). ${
							metrics.activeSciLabel ? `SCI active: ${metrics.activeSciLabel}.` : ''
						}`
					: 'Commence par le portefeuille pour cadrer la société, son régime fiscal et son contexte de pilotage.',
			href: '/scis',
			actionLabel:
				metrics.sciCount > 0 ? 'Ouvrir le portefeuille' : 'Créer ma première SCI',
			done: metrics.sciCount > 0,
			group: 'portfolio'
		},
		{
			key: 'associe',
			title:
				metrics.associeCount > 0
					? 'Gouvernance documentée'
					: 'Renseigner le premier associé',
			description:
				metrics.associeCount > 0
					? `${metrics.associeCount} associé(s) renseigné(s) avec part, rôle et rattachement.`
					: 'Ajoute ensuite la gouvernance réelle de la société pour éviter une SCI sans responsable métier.',
			href: '/associes',
			actionLabel:
				metrics.associeCount > 0 ? 'Contrôler la gouvernance' : 'Ajouter mon premier associé',
			done: metrics.associeCount > 0,
			group: 'portfolio'
		},
		{
			key: 'bien',
			title: metrics.bienCount > 0 ? 'Patrimoine rattaché' : 'Ajouter le premier bien',
			description:
				metrics.bienCount > 0
					? `${metrics.bienCount} bien(s) documenté(s) avec adresse, loyer, charges et fiscalité locative.`
					: 'Rattache ensuite un actif complet à la SCI active pour ouvrir l’exploitation locative.',
			href: '/biens',
			actionLabel: metrics.bienCount > 0 ? 'Voir les biens' : 'Ajouter mon premier bien',
			done: metrics.bienCount > 0,
			group: 'exploitation'
		},
		{
			key: 'locataire',
			title:
				metrics.locataireCount > 0
					? 'Occupation documentée'
					: 'Renseigner le premier locataire',
			description:
				metrics.locataireCount > 0
					? `${metrics.locataireCount} locataire(s) rattaché(s) à un bien avec période d’occupation.`
					: 'Ajoute ensuite l’occupant principal du bien avant de saisir les flux de loyer.',
			href: '/locataires',
			actionLabel:
				metrics.locataireCount > 0 ? 'Voir les locataires' : 'Ajouter mon premier locataire',
			done: metrics.locataireCount > 0,
			group: 'exploitation'
		},
		{
			key: 'loyer',
			title: metrics.loyerCount > 0 ? 'Encaissements actifs' : 'Saisir le premier loyer',
			description:
				metrics.loyerCount > 0
					? `${metrics.loyerCount} flux locatif(s) saisi(s), prêts pour recouvrement et quittances.`
					: 'Documente le premier encaissement pour activer le journal locatif et les documents PDF.',
			href: '/loyers',
			actionLabel:
				metrics.loyerCount > 0 ? 'Suivre les loyers' : 'Saisir mon premier loyer',
			done: metrics.loyerCount > 0,
			group: 'exploitation'
		},
		{
			key: 'charge',
			title:
				metrics.chargeCount > 0 ? 'Charges documentées' : 'Documenter la première charge',
			description:
				metrics.chargeCount > 0
					? `${metrics.chargeCount} charge(s) journalisée(s) pour piloter les sorties réelles.`
					: 'Renseigne la première charge pour sortir du pilotage purement théorique du patrimoine.',
			href: '/charges',
			actionLabel:
				metrics.chargeCount > 0 ? 'Contrôler les charges' : 'Ajouter ma première charge',
			done: metrics.chargeCount > 0,
			group: 'finance'
		},
		{
			key: 'fiscalite',
			title:
				metrics.fiscaliteCount > 0
					? 'Exercice fiscal ouvert'
					: 'Ouvrir le premier exercice fiscal',
			description:
				metrics.fiscaliteCount > 0
					? `${metrics.fiscaliteCount} exercice(s) consolidé(s) pour la lecture annuelle.`
					: 'Crée l’exercice fiscal pour consolider revenus, charges et résultat de la SCI.',
			href: '/fiscalite',
			actionLabel:
				metrics.fiscaliteCount > 0
					? 'Voir la fiscalité'
					: 'Ouvrir mon premier exercice',
			done: metrics.fiscaliteCount > 0,
			group: 'finance'
		}
	];

	if (scope === 'all') {
		return steps;
	}

	return steps.filter((step) => step.group === scope);
}
