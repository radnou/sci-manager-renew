<script lang="ts">
	import type { RentabiliteCalculee } from '$lib/api';
	import { apiFetch } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import { TrendingUp, TrendingDown, BarChart3, Table2, Loader2 } from 'lucide-svelte';
	import { onMount } from 'svelte';

	interface Props {
		rentabilite: RentabiliteCalculee;
		hasSourceData?: boolean;
		sciId?: string;
		bienId?: string;
	}

	let { rentabilite, hasSourceData = true, sciId = '', bienId = '' }: Props = $props();

	// Vue comptable annuelle
	type AnneeComptable = {
		annee: number;
		revenus: number;
		charges: number;
		evenements: number;
		resultat: number;
	};

	let vueComptable: AnneeComptable[] = $state([]);
	let comptaLoading = $state(false);

	onMount(async () => {
		if (!sciId || !bienId) return;
		comptaLoading = true;
		try {
			const currentYear = new Date().getFullYear();
			const years = [currentYear, currentYear - 1, currentYear - 2, currentYear - 3, currentYear - 4];
			const results: AnneeComptable[] = [];

			for (const year of years) {
				try {
					const compta = await apiFetch<any>(`/api/v1/scis/${sciId}/comptabilite/${year}`);
					const bien = (compta.biens || []).find((b: any) => b.bien_id === bienId);
					if (bien && (bien.revenus > 0 || bien.charges > 0)) {
						results.push({
							annee: year,
							revenus: bien.revenus || 0,
							charges: bien.charges || 0,
							evenements: bien.evenements_deductibles || 0,
							resultat: bien.resultat || 0,
						});
					}
				} catch { /* year not available */ }
			}

			vueComptable = results;
		} catch { /* ignore */ }
		comptaLoading = false;
	});

	// G12: Show warning only when source data (prix_acquisition + bail) is missing,
	// not when calculated values are legitimately 0.
	const isNoData = $derived(!hasSourceData);

	function cashflowColor(value: number): string {
		if (value > 0) return 'text-emerald-600 dark:text-emerald-400';
		if (value < 0) return 'text-rose-600 dark:text-rose-400';
		return 'text-slate-600 dark:text-slate-400';
	}

	function cashflowBg(value: number): string {
		if (value > 0) return 'bg-emerald-50 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800';
		if (value < 0) return 'bg-rose-50 border-rose-200 dark:bg-rose-950/30 dark:border-rose-800';
		return 'bg-slate-50 border-slate-200 dark:bg-slate-900 dark:border-slate-700';
	}
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center gap-2">
		<BarChart3 class="h-5 w-5 text-sky-600 dark:text-sky-400" />
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Rentabilité</h2>
	</div>

	{#if isNoData}
		<p class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
			Renseignez le prix d'acquisition et ajoutez un bail actif pour calculer la rentabilité.
		</p>
	{/if}

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		<!-- Rentabilité brute -->
		<div class="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
				Rentabilité brute
			</p>
			<p class="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
				{rentabilite.brute.toFixed(1)}%
			</p>
		</div>

		<!-- Rentabilité nette -->
		<div class="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
				Rentabilité nette
			</p>
			<p class="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
				{rentabilite.nette.toFixed(1)}%
			</p>
		</div>

		<!-- Cashflow mensuel -->
		<div class="rounded-xl border p-5 {cashflowBg(rentabilite.cashflow_mensuel)}">
			<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
				Cashflow mensuel
			</p>
			<div class="mt-1 flex items-center gap-1.5">
				{#if rentabilite.cashflow_mensuel >= 0}
					<TrendingUp class="h-4 w-4 {cashflowColor(rentabilite.cashflow_mensuel)}" />
				{:else}
					<TrendingDown class="h-4 w-4 {cashflowColor(rentabilite.cashflow_mensuel)}" />
				{/if}
				<p class="text-2xl font-bold {cashflowColor(rentabilite.cashflow_mensuel)}">
					{formatEur(rentabilite.cashflow_mensuel)}
				</p>
			</div>
		</div>

		<!-- Cashflow annuel -->
		<div class="rounded-xl border p-5 {cashflowBg(rentabilite.cashflow_annuel)}">
			<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
				Cashflow annuel
			</p>
			<div class="mt-1 flex items-center gap-1.5">
				{#if rentabilite.cashflow_annuel >= 0}
					<TrendingUp class="h-4 w-4 {cashflowColor(rentabilite.cashflow_annuel)}" />
				{:else}
					<TrendingDown class="h-4 w-4 {cashflowColor(rentabilite.cashflow_annuel)}" />
				{/if}
				<p class="text-2xl font-bold {cashflowColor(rentabilite.cashflow_annuel)}">
					{formatEur(rentabilite.cashflow_annuel)}
				</p>
			</div>
		</div>
	</div>

	{#if rentabilite.cashflow_apres_credit_mensuel !== 0 || rentabilite.cashflow_apres_credit_annuel !== 0}
		<div class="mt-4 grid gap-4 sm:grid-cols-2">
			<!-- Cashflow après crédit (mensuel) -->
			<div class="rounded-xl border p-5 {cashflowBg(rentabilite.cashflow_apres_credit_mensuel)}">
				<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
					Cashflow après crédit <span class="text-slate-400 dark:text-slate-500">/mois</span>
				</p>
				<div class="mt-1 flex items-center gap-1.5">
					{#if rentabilite.cashflow_apres_credit_mensuel >= 0}
						<TrendingUp class="h-4 w-4 {cashflowColor(rentabilite.cashflow_apres_credit_mensuel)}" />
					{:else}
						<TrendingDown class="h-4 w-4 {cashflowColor(rentabilite.cashflow_apres_credit_mensuel)}" />
					{/if}
					<p class="text-2xl font-bold {cashflowColor(rentabilite.cashflow_apres_credit_mensuel)}">
						{formatEur(rentabilite.cashflow_apres_credit_mensuel)}
					</p>
				</div>
			</div>
			<!-- Cashflow après crédit (annuel) -->
			<div class="rounded-xl border p-5 {cashflowBg(rentabilite.cashflow_apres_credit_annuel)}">
				<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
					Cashflow après crédit <span class="text-slate-400 dark:text-slate-500">/an</span>
				</p>
				<div class="mt-1 flex items-center gap-1.5">
					{#if rentabilite.cashflow_apres_credit_annuel >= 0}
						<TrendingUp class="h-4 w-4 {cashflowColor(rentabilite.cashflow_apres_credit_annuel)}" />
					{:else}
						<TrendingDown class="h-4 w-4 {cashflowColor(rentabilite.cashflow_apres_credit_annuel)}" />
					{/if}
					<p class="text-2xl font-bold {cashflowColor(rentabilite.cashflow_apres_credit_annuel)}">
						{formatEur(rentabilite.cashflow_apres_credit_annuel)}
					</p>
				</div>
			</div>
		</div>
	{/if}

	<!-- Vue comptable annuelle -->
	{#if comptaLoading}
		<div class="mt-6 flex items-center justify-center py-6">
			<Loader2 class="h-5 w-5 animate-spin text-slate-400" />
		</div>
	{:else if vueComptable.length > 0}
		<div class="mt-6">
			<div class="mb-3 flex items-center gap-2">
				<Table2 class="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
				<h3 class="text-sm font-semibold text-slate-700 dark:text-slate-300">Historique comptable</h3>
			</div>
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-slate-200 text-left text-xs font-medium text-slate-500 dark:border-slate-700 dark:text-slate-400">
							<th class="py-2.5 pr-4">Année</th>
							<th class="py-2.5 pr-4 text-right">Revenus</th>
							<th class="py-2.5 pr-4 text-right">Charges</th>
							<th class="py-2.5 pr-4 text-right">Événements</th>
							<th class="py-2.5 text-right">Résultat</th>
						</tr>
					</thead>
					<tbody>
						{#each vueComptable as row}
							<tr class="border-b border-slate-100 dark:border-slate-800">
								<td class="py-2.5 pr-4 font-semibold text-slate-900 dark:text-slate-100">{row.annee}</td>
								<td class="py-2.5 pr-4 text-right text-slate-700 dark:text-slate-300">{formatEur(row.revenus)}</td>
								<td class="py-2.5 pr-4 text-right text-slate-700 dark:text-slate-300">{formatEur(row.charges)}</td>
								<td class="py-2.5 pr-4 text-right text-slate-700 dark:text-slate-300">{formatEur(row.evenements)}</td>
								<td class="py-2.5 text-right font-semibold {row.resultat >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}">{formatEur(row.resultat)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>
