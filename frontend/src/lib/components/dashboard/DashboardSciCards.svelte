<script lang="ts">
	import { Building2 } from 'lucide-svelte';
	import type { SCICard } from '$lib/api';
	import EmptyState from '$lib/components/EmptyState.svelte';

	interface Props {
		scis: SCICard[];
	}

	let { scis }: Props = $props();

	function formatEur(value: number): string {
		return new Intl.NumberFormat('fr-FR', {
			style: 'currency',
			currency: 'EUR',
			maximumFractionDigits: 0
		}).format(value);
	}

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
</script>

{#if scis.length === 0}
	<EmptyState
		icon={Building2}
		title="Aucune SCI enregistree"
		description="Creez votre premiere SCI pour suivre vos biens, loyers et charges depuis le dashboard."
		ctaText="Creer une SCI"
		ctaHref="/scis"
	/>
{:else}
	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
		{#each scis as sci (sci.id)}
			<a
				href="/scis/{sci.id}"
				class="group rounded-xl border border-slate-200 bg-white p-5 transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700"
			>
				<div class="flex items-start justify-between">
					<h3
						class="text-sm font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-slate-100 dark:group-hover:text-indigo-400"
					>
						{sci.nom}
					</h3>
					<span
						class="rounded-full px-2 py-0.5 text-[0.65rem] font-semibold {statutBadge[sci.statut] ?? statutBadge['configuration']}"
					>
						{statutLabel[sci.statut] ?? sci.statut}
					</span>
				</div>

				<div class="mt-4 space-y-2">
					<div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
						<span>{sci.biens_count} bien{sci.biens_count > 1 ? 's' : ''}</span>
						<span class="font-medium text-slate-900 dark:text-slate-100">
							{formatEur(sci.loyer_total)}/mois
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
				</div>
			</a>
		{/each}
	</div>
{/if}
