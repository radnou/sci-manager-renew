<script lang="ts">
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import { formatPercent } from '$lib/high-value/formatters';

	interface Props {
		bienMetrics: {
			count: number;
			totalMonthlyRentLabel: string;
		};
		loyerMetrics: {
			totalPaidLabel: string;
			totalOutstanding: number;
			totalRecordedLabel: string;
			lateCount: number;
		};
		collectionRate: number;
		loading: boolean;
	}

	let { bienMetrics, loyerMetrics, collectionRate, loading }: Props = $props();
</script>

<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
	<KpiCard
		label="Biens actifs"
		value={bienMetrics.count}
		caption="actifs rattachés à la SCI"
		trend="up"
		trendValue="patrimoine"
		tone="accent"
		{loading}
	/>
	<KpiCard
		label="Loyers de la SCI active"
		value={bienMetrics.totalMonthlyRentLabel}
		caption="potentiel mensuel sécurisé"
		trend="up"
		trendValue="revenus"
		tone="success"
		{loading}
	/>
	<KpiCard
		label="Flux encaissés"
		value={loyerMetrics.totalPaidLabel}
		caption="encaissements réellement payés"
		trend="neutral"
		trendValue={loyerMetrics.totalOutstanding > 0 ? 'à suivre' : 'sécurisé'}
		tone="default"
		{loading}
	/>
	<KpiCard
		label="Recouvrement"
		value={formatPercent(collectionRate, '0%')}
		caption={`${loyerMetrics.totalPaidLabel} encaissés sur ${loyerMetrics.totalRecordedLabel}`}
		trend={loyerMetrics.lateCount > 0 ? 'down' : loyerMetrics.totalOutstanding > 0 ? 'neutral' : 'up'}
		trendValue={loyerMetrics.lateCount > 0 ? 'vigilance' : loyerMetrics.totalOutstanding > 0 ? 'à compléter' : 'conforme'}
		tone={loyerMetrics.lateCount > 0 ? 'warning' : loyerMetrics.totalOutstanding > 0 ? 'default' : 'accent'}
		{loading}
	/>
</div>
