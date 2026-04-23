<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { ChevronDown, ChevronUp } from 'lucide-svelte';
	import { trackEvent, EVENTS } from '$lib/analytics';

	let { openFaqIndex = $bindable(null) }: { openFaqIndex?: number | null } = $props();

	const faqItems = [
		{
			question: "Mon comptable s'occupe déjà de tout",
			answer:
				"Votre comptable intervient en fin d'année pour la déclaration. GérerSCI vous aide au quotidien : suivi des loyers, relances automatiques, quittances, charges. Vous arrivez chez votre comptable avec des données propres et structurées — il vous en remerciera."
		},
		{
			question: "19€/mois c'est trop cher",
			answer:
				"Un retard de loyer non détecté vous coûte 800€ minimum. Une erreur sur la 2044 peut déclencher un contrôle fiscal. GérerSCI remplace en moyenne 150€/mois de prestations (quittances, suivi comptable, gestion locative). C'est 6x moins cher que le minimum."
		},
		{
			question: "J'ai seulement 1 bien",
			answer:
				"Le plan Gestion à 19€/mois est conçu pour vous. Un seul bien mal géré peut coûter des milliers d'euros en impayés ou en erreurs fiscales. Et quand vous ajouterez un deuxième bien, tout sera déjà en place."
		},
		{
			question: 'Mes données sont-elles sécurisées ?',
			answer:
				'Hébergement UE via Supabase (PostgreSQL), isolation des données par SCI avec Row-Level Security, chiffrement en transit et au repos. Espace confidentialité dédié avec export JSON et suppression de compte. Conforme RGPD.'
		},
		{
			question: 'Je peux faire ça avec Excel',
			answer:
				"Vous pouvez. Mais Excel ne génère pas de quittances PDF conformes, ne calcule pas votre CERFA 2044, ne vous alerte pas sur un loyer en retard, et ne produit pas de calendrier fiscal. GérerSCI fait tout ça en 10 minutes par mois."
		},
		{
			question: 'Et si je veux annuler ?',
			answer:
				"Annulation en 1 clic depuis votre espace. Pas de période d'engagement, pas de frais cachés. Vos données restent accessibles 30 jours après annulation. Garantie satisfait ou remboursé 30 jours."
		},
		{
			question: "Je ne suis pas à l'aise avec l'informatique",
			answer:
				"L'onboarding guidé vous accompagne pas à pas : créer votre SCI, ajouter un bien, configurer un bail. En 5 minutes, vous êtes opérationnel. Et le support répond sous 48h (24h en Pilotage)."
		},
		{
			question: "C'est un nouveau produit",
			answer:
				"GérerSCI est développé par des gérants de SCI, pour des gérants de SCI. Le produit est en production, utilisé quotidiennement. L'offre Fondateur vous donne un accès à vie au meilleur prix — et un accès beta à toutes les nouvelles fonctionnalités."
		},
		{
			question: "Est-ce que ça remplace la déclaration fiscale ?",
			answer:
				"Non. GérerSCI prépare vos données fiscales : résumé CERFA 2044, résultat foncier, répartition par associé. Votre comptable ou vous-même restez responsable de la déclaration finale. Les calculs sont fournis à titre indicatif."
		},
		{
			question: "Pourquoi pas d'offre gratuite ?",
			answer:
				"Un outil gratuit ne peut pas offrir un support de qualité, des mises à jour régulières et la sécurité que vos données méritent. Le plan Gestion à 19€/mois vous donne un outil professionnel complet. Garantie 30 jours satisfait ou remboursé — si l'outil ne vous convient pas, on vous rembourse sans condition."
		}
	];

	function toggleFaq(i: number) {
		if (openFaqIndex !== i) {
			trackEvent(EVENTS.LANDING_FAQ_OPEN, { question: i });
		}
		openFaqIndex = openFaqIndex === i ? null : i;
	}
</script>

<section class="bg-white py-20 dark:bg-slate-900">
	<div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
		<div class="mb-12 text-center">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Questions fréquentes</Badge>
			<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
				Tout ce que vous devez savoir
			</h2>
		</div>

		<div class="space-y-3">
			{#each faqItems as item, i}
				<div
					class="rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800"
				>
					<button
						class="flex w-full items-center justify-between rounded-2xl px-6 py-5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
						aria-expanded={openFaqIndex === i}
						onclick={() => toggleFaq(i)}
					>
						<span class="pr-4 text-base font-semibold text-slate-900 dark:text-slate-100">
							{item.question}
						</span>
						{#if openFaqIndex === i}
							<ChevronUp
								class="h-5 w-5 flex-shrink-0 text-slate-400 dark:text-slate-500"
							/>
						{:else}
							<ChevronDown
								class="h-5 w-5 flex-shrink-0 text-slate-400 dark:text-slate-500"
							/>
						{/if}
					</button>
					<div
						class="overflow-hidden px-6 text-sm leading-relaxed text-slate-600 transition-all duration-200 dark:text-slate-400 {openFaqIndex === i ? 'max-h-96 pb-5' : 'max-h-0'}"
					>
						{item.answer}
					</div>
				</div>
			{/each}
		</div>
	</div>
</section>
