<script lang="ts">
	import type { FinancesData } from '$lib/api';
	import { fetchFinances, exportLoyersCsv } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import {
		TrendingUp,
		TrendingDown,
		Wallet,
		Building,
		BarChart3,
		Percent,
		RefreshCw,
		Download
	} from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { addToast } from '$lib/components/ui/toast';

	let data: FinancesData | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);
	let period = $state('12m');
	let exportingLoyers = $state(false);

	async function handleExportLoyers() {
		exportingLoyers = true;
		try {
			const blob = await exportLoyersCsv(undefined, period);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `loyers_export_${new Date().toISOString().slice(0, 10)}.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			addToast({ title: 'Export terminé', description: 'Le fichier CSV des loyers a été téléchargé.', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur export', description: err?.message ?? "Impossible d'exporter les loyers.", variant: 'error' });
		} finally {
			exportingLoyers = false;
		}
	}

	$effect(() => {
		loadFinances(period);
	});

	async function loadFinances(p: string) {
		loading = true;
		error = null;
		try {
			data = await fetchFinances(p);
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger les finances.';
			data = null;
		} finally {
			loading = false;
		}
	}

	function cashflowColor(value: number): string {
		if (value > 0) return 'text-emerald-600 dark:text-emerald-400';
		if (value < 0) return 'text-rose-600 dark:text-rose-400';
		return 'text-slate-700 dark:text-slate-300';
	}

	function maxBarValue(items: Array<{ revenus: number; charges: number }>): number {
		if (items.length === 0) return 1;
		return Math.max(...items.map((i) => Math.max(i.revenus, i.charges)), 1);
	}
</script>

<svelte:head><title>Finances | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Transversal</p>
		<h1 class="sci-page-title">Finances</h1>
	</header>

	<!-- Period selector + export -->
	<div class="mt-4 flex items-center justify-between gap-4">
		<div class="flex items-center gap-2">
			{#each ['6m', '12m', '24m'] as p}
				<button
					onclick={() => (period = p)}
					class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {period === p
						? 'bg-sky-600 text-white'
						: 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700'}"
				>
					{p === '6m' ? '6 mois' : p === '12m' ? '12 mois' : '24 mois'}
				</button>
			{/each}
		</div>
		<Button onclick={handleExportLoyers} disabled={exportingLoyers} variant="outline" class="shrink-0">
			<Download class="mr-2 h-4 w-4" />
			{exportingLoyers ? 'Export...' : 'Exporter les loyers (CSV)'}
		</Button>
	</div>

	{#if loading}
		<div class="sci-loading" aria-label="Chargement"></div>
	{:else if error}
		<div
			class="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30"
		>
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={() => loadFinances(period)}
				class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				<RefreshCw class="h-4 w-4" />
				Réessayer
			</button>
		</div>
	{:else if data && data.revenus_total === 0 && data.charges_total === 0 && data.repartition_sci.length === 0}
		<div class="mt-6">
			<EmptyState
				icon={Wallet}
				title="Aucune donnée financière"
				description="Enregistrez des loyers et des charges sur vos biens pour voir apparaître vos revenus, cashflow et graphiques d'évolution."
				ctaText="Aller au dashboard"
				ctaHref="/dashboard"
			/>
		</div>
	{:else if data}
		<!-- KPI cards -->
		<div class="sci-stagger mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			<!-- Revenus total -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<TrendingUp class="h-5 w-5 text-emerald-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Revenus
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
					{formatEur(data.revenus_total)}
				</p>
			</div>

			<!-- Charges total -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<TrendingDown class="h-5 w-5 text-rose-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Charges
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
					{formatEur(data.charges_total)}
				</p>
			</div>

			<!-- Cashflow net -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<Wallet class="h-5 w-5 text-sky-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Cashflow net
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold {cashflowColor(data.cashflow_net)}">
					{formatEur(data.cashflow_net)}
				</p>
			</div>

			<!-- Patrimoine -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<Building class="h-5 w-5 text-indigo-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Patrimoine
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
					{formatEur(data.patrimoine_total)}
				</p>
			</div>

			<!-- Taux de recouvrement -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<Percent class="h-5 w-5 text-amber-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Recouvrement
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
					{data.taux_recouvrement.toFixed(1)}%
				</p>
			</div>

			<!-- Rentabilité moyenne -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<BarChart3 class="h-5 w-5 text-teal-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Rentabilité moy.
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
					{data.rentabilite_moyenne.toFixed(1)}%
				</p>
			</div>
		</div>

		<!-- Évolution mensuelle -->
		{#if data.evolution_mensuelle.length > 0}
			<div
				class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
			>
				<h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
					Évolution mensuelle
				</h2>

				<!-- Bar chart using CSS -->
				<div class="space-y-2">
					{#each data.evolution_mensuelle as month}
						{@const max = maxBarValue(data.evolution_mensuelle)}
						<div class="flex items-center gap-3 text-sm">
							<span
								class="w-16 shrink-0 text-xs font-medium text-slate-500 dark:text-slate-400"
							>
								{month.mois}
							</span>
							<div class="flex-1 space-y-1">
								<div class="flex items-center gap-2">
									<div
										class="h-3 rounded bg-emerald-500/80"
										style="width: {Math.max((month.revenus / max) * 100, 1)}%"
									></div>
									<span class="text-xs text-emerald-700 dark:text-emerald-400">
										{formatEur(month.revenus)}
									</span>
								</div>
								<div class="flex items-center gap-2">
									<div
										class="h-3 rounded bg-rose-500/80"
										style="width: {Math.max((month.charges / max) * 100, 1)}%"
									></div>
									<span class="text-xs text-rose-700 dark:text-rose-400">
										{formatEur(month.charges)}
									</span>
								</div>
							</div>
						</div>
					{/each}
				</div>

				<div class="mt-4 flex items-center gap-4 text-xs text-slate-500">
					<div class="flex items-center gap-1.5">
						<div class="h-2.5 w-2.5 rounded bg-emerald-500/80"></div>
						Revenus
					</div>
					<div class="flex items-center gap-1.5">
						<div class="h-2.5 w-2.5 rounded bg-rose-500/80"></div>
						Charges
					</div>
				</div>
			</div>
		{/if}

		<!-- Répartition par SCI -->
		{#if data.repartition_sci.length > 0}
			<div
				class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
			>
				<h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
					Répartition par SCI
				</h2>

				<div class="overflow-x-auto">
					<table class="w-full text-left text-sm">
						<thead>
							<tr class="border-b border-slate-200 dark:border-slate-700">
								<th
									class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>
									SCI
								</th>
								<th
									class="pb-3 pr-4 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>
									Revenus
								</th>
								<th
									class="pb-3 pr-4 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>
									Charges
								</th>
								<th
									class="pb-3 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>
									Cashflow
								</th>
							</tr>
						</thead>
						<tbody>
							{#each data.repartition_sci as sci}
								{@const cf = sci.revenus - sci.charges}
								<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
									<td class="py-3 pr-4 font-medium text-slate-900 dark:text-slate-100">
										{sci.sci_nom}
									</td>
									<td class="py-3 pr-4 text-right text-emerald-700 dark:text-emerald-400">
										{formatEur(sci.revenus)}
									</td>
									<td class="py-3 pr-4 text-right text-rose-700 dark:text-rose-400">
										{formatEur(sci.charges)}
									</td>
									<td class="py-3 text-right font-semibold {cashflowColor(cf)}">
										{formatEur(cf)}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}
	{/if}
</section>
