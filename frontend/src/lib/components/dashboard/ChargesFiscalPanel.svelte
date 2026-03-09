<script lang="ts">
	import type { Charge, Fiscalite } from '$lib/api';
	import { FileText } from 'lucide-svelte';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { mapChargeTypeLabel } from '$lib/high-value/presentation';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';

	interface Props {
		totalRecordedCharges: number | null | undefined;
		chargesCount: number;
		recentCharges: Charge[];
		latestFiscalYear: Fiscalite | null;
		detailLoading: boolean;
	}

	let {
		totalRecordedCharges,
		chargesCount,
		recentCharges,
		latestFiscalYear,
		detailLoading
	}: Props = $props();
</script>

<Card class="sci-section-card">
	<CardHeader>
		<CardTitle class="flex items-center gap-2 text-lg">
			<FileText class="h-5 w-5 text-emerald-600" />
			Charges et fiscalité
		</CardTitle>
		<CardDescription>
			Signaux spécifiques à la SCI active pour la clôture et la conformité.
		</CardDescription>
	</CardHeader>
	<CardContent class="space-y-4 pt-0">
		{#if detailLoading}
			<div class="space-y-3">
				{#each Array.from({ length: 3 }) as _}
					<div class="h-20 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
				{/each}
			</div>
		{:else}
			<div
				class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
			>
				<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
					Charges documentées
				</p>
				<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
					{formatEur(totalRecordedCharges, 'N/A')}
				</p>
				<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
					{chargesCount} mouvement(s) documenté(s) sur la SCI active.
				</p>
			</div>

			<div class="space-y-3">
				{#if recentCharges.length}
					{#each recentCharges.slice(0, 2) as charge (String(charge.id || `${charge.id_bien}-${charge.date_paiement}`))}
						<div
							class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950"
						>
							<div class="flex items-center justify-between gap-3">
								<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
									{mapChargeTypeLabel(charge.type_charge)}
								</p>
								<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
									{formatEur(charge.montant, 'N/A')}
								</p>
							</div>
							<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
								Payée le {formatFrDate(charge.date_paiement)}
							</p>
						</div>
					{/each}
				{:else}
					<div
						class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
					>
						Aucune charge récente documentée pour cette SCI.
					</div>
				{/if}
			</div>

			<div
				class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
			>
				<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
					Dernier exercice fiscal
				</p>
				{#if latestFiscalYear}
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						Exercice {latestFiscalYear.annee}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Résultat {formatEur(latestFiscalYear.resultat_fiscal, 'N/A')} • revenus {formatEur(
							latestFiscalYear.total_revenus,
							'N/A'
						)}
					</p>
				{:else}
					<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
						Aucun exercice consolidé pour la SCI active.
					</p>
				{/if}
			</div>
		{/if}
	</CardContent>
</Card>
