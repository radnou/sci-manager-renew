<script lang="ts">
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import { formatCompactNumber, formatPercent } from '$lib/high-value/formatters';
	import type { PortfolioMetrics } from '$lib/high-value/portfolio';

	interface Props {
		metrics: PortfolioMetrics;
		loading: boolean;
	}

	let { metrics, loading }: Props = $props();
</script>

<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
	<KpiCard
		label="SCI suivies"
		value={formatCompactNumber(metrics.sciCount)}
		caption={`${metrics.operationalSciCount} opérationnelle(s) dans le portefeuille`}
		trend={metrics.attentionSciCount > 0 ? 'neutral' : 'up'}
		trendValue={metrics.attentionSciCount > 0
			? `${metrics.attentionSciCount} à surveiller`
			: 'sous contrôle'}
		tone={metrics.attentionSciCount > 0 ? 'warning' : 'accent'}
		{loading}
	/>
	<KpiCard
		label="Patrimoine consolidé"
		value={metrics.bienMetrics.count}
		caption="biens rattachés à l'ensemble du compte"
		trend="up"
		trendValue="multi-SCI"
		tone="accent"
		{loading}
	/>
	<KpiCard
		label="Loyer cible global"
		value={metrics.bienMetrics.totalMonthlyRentLabel}
		caption="potentiel mensuel sur l'ensemble des SCI"
		trend="up"
		trendValue="portefeuille"
		tone="success"
		{loading}
	/>
	<KpiCard
		label="Recouvrement"
		value={formatPercent(metrics.loyerMetrics.collectionRate, '0%')}
		caption={`${metrics.loyerMetrics.totalPaidLabel} encaissés sur ${metrics.loyerMetrics.totalRecordedLabel}`}
		trend={metrics.loyerMetrics.lateCount > 0
			? 'down'
			: metrics.loyerMetrics.totalOutstanding > 0
				? 'neutral'
				: 'up'}
		trendValue={metrics.loyerMetrics.lateCount > 0
			? 'vigilance'
			: metrics.loyerMetrics.totalOutstanding > 0
				? 'à compléter'
				: 'conforme'}
		tone={metrics.loyerMetrics.lateCount > 0
			? 'warning'
			: metrics.loyerMetrics.totalOutstanding > 0
				? 'default'
				: 'accent'}
		{loading}
	/>
</div>
