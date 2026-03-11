<script lang="ts">
	import { Building2, Landmark, TrendingUp, Wallet } from 'lucide-svelte';
	import type { DashboardKpis } from '$lib/api';

	interface Props {
		kpis: DashboardKpis;
	}

	let { kpis }: Props = $props();

	function formatEur(value: number): string {
		return new Intl.NumberFormat('fr-FR', {
			style: 'currency',
			currency: 'EUR',
			maximumFractionDigits: 0
		}).format(value);
	}

	function formatPercent(value: number): string {
		return new Intl.NumberFormat('fr-FR', {
			style: 'percent',
			minimumFractionDigits: 0,
			maximumFractionDigits: 1
		}).format(value / 100);
	}

	const cards = $derived([
		{
			label: 'SCI actives',
			value: String(kpis.sci_count),
			icon: Landmark,
			iconColor: 'text-indigo-500 dark:text-indigo-400',
			bgIcon: 'bg-indigo-50 dark:bg-indigo-950/40'
		},
		{
			label: 'Biens',
			value: String(kpis.biens_count),
			icon: Building2,
			iconColor: 'text-sky-500 dark:text-sky-400',
			bgIcon: 'bg-sky-50 dark:bg-sky-950/40'
		},
		{
			label: 'Recouvrement',
			value: formatPercent(kpis.taux_recouvrement),
			icon: TrendingUp,
			iconColor:
				kpis.taux_recouvrement >= 80
					? 'text-emerald-500 dark:text-emerald-400'
					: 'text-amber-500 dark:text-amber-400',
			bgIcon:
				kpis.taux_recouvrement >= 80
					? 'bg-emerald-50 dark:bg-emerald-950/40'
					: 'bg-amber-50 dark:bg-amber-950/40'
		},
		{
			label: 'Cashflow net',
			value: formatEur(kpis.cashflow_net),
			icon: Wallet,
			iconColor:
				kpis.cashflow_net >= 0
					? 'text-emerald-500 dark:text-emerald-400'
					: 'text-rose-500 dark:text-rose-400',
			bgIcon:
				kpis.cashflow_net >= 0
					? 'bg-emerald-50 dark:bg-emerald-950/40'
					: 'bg-rose-50 dark:bg-rose-950/40'
		}
	]);
</script>

<div class="grid gap-4 grid-cols-2 md:grid-cols-4">
	{#each cards as card (card.label)}
		<div
			class="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
		>
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-lg {card.bgIcon}">
					<card.icon class="h-5 w-5 {card.iconColor}" />
				</div>
				<div class="min-w-0">
					<p class="text-xs font-medium text-slate-500 dark:text-slate-400">{card.label}</p>
					<p class="text-xl font-bold text-slate-900 dark:text-slate-100">{card.value}</p>
				</div>
			</div>
		</div>
	{/each}
</div>
