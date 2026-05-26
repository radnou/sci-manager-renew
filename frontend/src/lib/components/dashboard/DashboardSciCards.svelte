<script lang="ts">
	import { Building2, Receipt } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import type { SCICard } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import EmptyState from '$lib/components/EmptyState.svelte';

	interface Props {
		scis: SCICard[];
	}

	let { scis }: Props = $props();

	const statutBadge: Record<string, string> = {
		configuration:
			'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
		mise_en_service:
			'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
		exploitation:
			'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
	};

	const statutLabel: Record<string, string> = {
		configuration: 'Configuration',
		mise_en_service: 'Mise en service',
		exploitation: 'Exploitation'
	};

	const loyerStatusColor: Record<string, string> = {
		paye: 'text-emerald-600 dark:text-emerald-400',
		en_attente: 'text-amber-600 dark:text-amber-400',
		en_retard: 'text-rose-600 dark:text-rose-400',
		retard: 'text-rose-600 dark:text-rose-400',
	};

	function getLoyerStatusText(sci: SCICard): string {
		if (!sci.dernier_loyer) return 'Aucun loyer enregistré';
		const { montant, date_paiement, statut } = sci.dernier_loyer;
		if (!montant) return 'Dernier loyer sans montant';
		if (statut === 'paye' && date_paiement) {
			return `${formatEur(montant)} — Payé le ${formatFrDate(date_paiement)}`;
		}
		return `${formatEur(montant)} — ${statut || 'Statut inconnu'}`;
	}
</script>

{#if scis.length === 0}
	<EmptyState
		icon={Building2}
		title="Aucune SCI enregistrée"
		description="Créez votre première SCI pour suivre vos biens, loyers et charges depuis le dashboard."
		ctaText="Créer une SCI"
		ctaHref="/scis"
	/>
{:else}
	<div class="sci-stagger grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
		{#each scis as sci (sci.id)}
			<a
				href={`/scis/${sci.id}`}
				class="group rounded-xl border border-slate-200 bg-white p-5 transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700"
			>
				<div class="flex items-start justify-between">
					<h3
						class="text-sm font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-slate-100 dark:group-hover:text-indigo-400"
					>
						{sci.nom}
					</h3>
					<span
						class="rounded-full px-2 py-0.5 text-xs font-semibold {statutBadge[sci.statut] ?? statutBadge['configuration']}"
					>
						{statutLabel[sci.statut] ?? sci.statut}
					</span>
				</div>

				<div class="mt-4 space-y-2">
					<div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
						<span>{sci.biens_count} bien{sci.biens_count > 1 ? 's' : ''}</span>
						<span class="font-medium text-slate-900 dark:text-slate-100">
							{formatEur(sci.loyer_total)}
						</span>
					</div>

					<div>
						<div class="flex items-center justify-between text-xs">
							<span class="text-slate-500 dark:text-slate-400">Recouvrement</span>
							<span class="font-medium text-slate-700 dark:text-slate-300">
								{Math.round(sci.recouvrement)}%
							</span>
						</div>
						<div
							class="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"
						>
							<div
								class="h-full rounded-full transition-all {sci.recouvrement >= 80
									? 'bg-emerald-500'
									: sci.recouvrement >= 50
										? 'bg-amber-500'
										: 'bg-rose-500'}"
								style="width: {Math.min(sci.recouvrement, 100)}%"
							></div>
						</div>
					</div>

  						<!-- Last loyer status -->
							<div class="mt-3 flex items-start gap-2 text-xs">
								<Receipt class="mt-0.5 h-3.5 w-3.5 flex-shrink-0 {loyerStatusColor[sci.dernier_loyer?.statut || ''] ?? 'text-slate-400 dark:text-slate-500'}"
								/>
								<span class="text-slate-600 dark:text-slate-400">
									<span class="font-medium">Dernier loyer:</span> {getLoyerStatusText(sci)}
								</span>
							</div>

							<!-- Quick access to biens -->
							<div class="mt-3 border-t border-slate-100 pt-2 dark:border-slate-800">
								<button
									type="button"
									class="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
									onclick={(e) => {
										e.preventDefault();
										e.stopPropagation();
										goto(`/scis/${sci.id}/biens`);
									}}
								>
									Voir les {sci.biens_count} bien{sci.biens_count > 1 ? 's' : ''} &rarr;
								</button>
							</div>
						</div>
					</a>
				{/each}
			</div>
		{/if}
