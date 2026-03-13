<script lang="ts">
	import { Building2, Landmark, TrendingUp, Wallet, BarChart3 } from 'lucide-svelte';
	import type { DashboardKpis } from '$lib/api';
	import EmptyState from '$lib/components/EmptyState.svelte';

	interface Props {
		kpis: DashboardKpis;
	}

	let { kpis }: Props = $props();

	const isEmpty = $derived(
		kpis.sci_count === 0 && kpis.biens_count === 0 && kpis.taux_recouvrement === 0 && kpis.cashflow_net === 0
	);

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

	const noLoyers = $derived(kpis.taux_recouvrement === 0 && kpis.cashflow_net === 0 && kpis.biens_count > 0);

	const cards = $derived([
		{
			label: 'SCI actives',
			value: String(kpis.sci_count),
			hint: kpis.sci_count === 0 ? 'Créez votre première SCI' : '',
			icon: Landmark,
			iconColor: 'text-indigo-500 dark:text-indigo-400',
			bgIcon: 'bg-indigo-50 dark:bg-indigo-950/40'
		},
		{
			label: 'Biens',
			value: String(kpis.biens_count),
			hint: kpis.biens_count === 0 && kpis.sci_count > 0 ? 'Ajoutez un bien à une SCI' : '',
			icon: Building2,
			iconColor: 'text-sky-500 dark:text-sky-400',
			bgIcon: 'bg-sky-50 dark:bg-sky-950/40'
		},
		{
			label: 'Recouvrement',
			value: noLoyers ? '—' : formatPercent(kpis.taux_recouvrement),
			hint: noLoyers ? 'Enregistrez un loyer pour activer' : '',
			icon: TrendingUp,
			iconColor: noLoyers
				? 'text-slate-400 dark:text-slate-500'
				: kpis.taux_recouvrement >= 80
					? 'text-emerald-500 dark:text-emerald-400'
					: 'text-amber-500 dark:text-amber-400',
			bgIcon: noLoyers
				? 'bg-slate-100 dark:bg-slate-800'
				: kpis.taux_recouvrement >= 80
					? 'bg-emerald-50 dark:bg-emerald-950/40'
					: 'bg-amber-50 dark:bg-amber-950/40'
		},
		{
			label: 'Cashflow net',
			value: noLoyers ? '—' : formatEur(kpis.cashflow_net),
			hint: noLoyers ? 'Enregistrez un loyer pour activer' : '',
			icon: Wallet,
			iconColor: noLoyers
				? 'text-slate-400 dark:text-slate-500'
				: kpis.cashflow_net >= 0
					? 'text-emerald-500 dark:text-emerald-400'
					: 'text-rose-500 dark:text-rose-400',
			bgIcon: noLoyers
				? 'bg-slate-100 dark:bg-slate-800'
				: kpis.cashflow_net >= 0
					? 'bg-emerald-50 dark:bg-emerald-950/40'
					: 'bg-rose-50 dark:bg-rose-950/40'
		}
	]);
</script>

{#if isEmpty}
	<EmptyState
		icon={BarChart3}
		title="Vos indicateurs apparaîtront ici"
		description="Enregistrez votre première SCI et un loyer pour voir vos KPIs : nombre de biens, taux de recouvrement, cashflow net."
		ctaText="Créer une SCI"
		ctaHref="/scis"
	/>
{:else}
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
						{#if card.hint}
							<p class="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{card.hint}</p>
						{/if}
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}
