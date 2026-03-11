<script lang="ts">
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { Plus, FileText, Check } from 'lucide-svelte';

	interface Props {
		loyers: Array<any>;
		isGerant: boolean;
		sciId: string | number;
		bienId: string | number;
	}

	let { loyers, isGerant, sciId, bienId }: Props = $props();

	const statutConfig: Record<string, { label: string; class: string }> = {
		paye: {
			label: 'Payé',
			class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
		},
		en_attente: {
			label: 'En attente',
			class: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
		},
		en_retard: {
			label: 'En retard',
			class: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
		},
		retard: {
			label: 'En retard',
			class: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
		}
	};

	function getStatut(statut: string | null | undefined) {
		if (!statut) return statutConfig['en_attente'];
		return statutConfig[statut] ?? { label: statut, class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' };
	}
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Loyers</h2>
		{#if isGerant}
			<button
				class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
			>
				<Plus class="h-4 w-4" />
				Enregistrer un loyer
			</button>
		{/if}
	</div>

	{#if loyers.length === 0}
		<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700">
			<p class="text-sm text-slate-500 dark:text-slate-400">Aucun loyer enregistré pour ce bien.</p>
			{#if isGerant}
				<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
					Cliquez sur "Enregistrer un loyer" pour commencer.
				</p>
			{/if}
		</div>
	{:else}
		<div class="overflow-x-auto">
			<table class="w-full text-left text-sm">
				<thead>
					<tr class="border-b border-slate-200 dark:border-slate-700">
						<th class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Mois
						</th>
						<th class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Montant
						</th>
						<th class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Statut
						</th>
						<th class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Date paiement
						</th>
						{#if isGerant}
							<th class="pb-3 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
								Actions
							</th>
						{/if}
					</tr>
				</thead>
				<tbody>
					{#each loyers as loyer (loyer.id ?? loyer.date_loyer)}
						{@const statut = getStatut(loyer.statut)}
						<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
							<td class="py-3 pr-4 font-medium text-slate-900 dark:text-slate-100">
								{formatFrDate(loyer.date_loyer)}
							</td>
							<td class="py-3 pr-4 text-slate-700 dark:text-slate-300">
								{formatEur(loyer.montant)}
							</td>
							<td class="py-3 pr-4">
								<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {statut.class}">
									{statut.label}
								</span>
							</td>
							<td class="py-3 pr-4 text-slate-500 dark:text-slate-400">
								{loyer.date_paiement ? formatFrDate(loyer.date_paiement) : '—'}
							</td>
							{#if isGerant}
								<td class="py-3">
									<div class="flex gap-2">
										{#if loyer.statut !== 'paye'}
											<button
												class="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 transition-colors hover:bg-emerald-100 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400"
												title="Marquer comme payé"
											>
												<Check class="h-3 w-3" />
												Payé
											</button>
										{/if}
										<button
											class="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
											title="Générer la quittance"
										>
											<FileText class="h-3 w-3" />
											Quittance
										</button>
									</div>
								</td>
							{/if}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
