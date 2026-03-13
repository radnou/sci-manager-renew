<script lang="ts">
	import type { RentabiliteCalculee } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-svelte';

	interface Props {
		rentabilite: RentabiliteCalculee;
		hasSourceData?: boolean;
	}

	let { rentabilite, hasSourceData = true }: Props = $props();

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
			Renseignez le prix d'acquisition et ajoutez un bail actif pour calculer la rentabilite.
		</p>
	{/if}

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		<!-- Rentabilité brute -->
		<div class="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase dark:text-slate-400">
				Rentabilité brute
			</p>
			<p class="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
				{rentabilite.brute.toFixed(1)}%
			</p>
		</div>

		<!-- Rentabilité nette -->
		<div class="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase dark:text-slate-400">
				Rentabilité nette
			</p>
			<p class="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
				{rentabilite.nette.toFixed(1)}%
			</p>
		</div>

		<!-- Cashflow mensuel -->
		<div class="rounded-xl border p-5 {cashflowBg(rentabilite.cashflow_mensuel)}">
			<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase dark:text-slate-400">
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
			<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase dark:text-slate-400">
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
</div>
