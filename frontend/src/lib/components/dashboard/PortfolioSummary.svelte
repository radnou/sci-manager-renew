<script lang="ts">
	import type { PortfolioMetrics } from '$lib/high-value/portfolio';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';

	interface Props {
		metrics: PortfolioMetrics;
	}

	let { metrics }: Props = $props();
</script>

<Card id="dashboard-governance" class="sci-section-card scroll-mt-28">
	<CardHeader>
		<CardTitle class="text-lg">Vue portefeuille</CardTitle>
		<CardDescription>
			Vue consolidée pour arbitrer entre structuration, trésorerie et priorités.
		</CardDescription>
	</CardHeader>
	<CardContent class="space-y-4 pt-0">
		<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">SCI opérationnelles</p>
			<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
				{metrics.operationalSciCount}/{metrics.sciCount}
			</p>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
				{metrics.setupSciCount > 0
					? `${metrics.setupSciCount} société(s) restent à structurer.`
					: 'Toutes les SCI du portefeuille sont mises en service ou en exploitation.'}
			</p>
		</div>

		<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Trésorerie consolidée</p>
			<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
				{metrics.loyerMetrics.totalOutstandingLabel}
			</p>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
				restent à encaisser sur {metrics.loyerMetrics.totalRecordedLabel} saisis.
			</p>
		</div>

		<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Points de vigilance</p>
			<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
				{metrics.attentionSciCount}
			</p>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
				SCI demandent une action, avec {metrics.loyerMetrics.lateCount} retard(s) identifié(s).
			</p>
		</div>

		<div class="flex flex-wrap gap-2">
			<a href="/scis"><Button variant="outline" size="sm">Voir les SCI</Button></a>
			<a href="/biens"><Button size="sm">Gérer les biens</Button></a>
			<a href="/loyers"><Button variant="outline" size="sm">Suivre les loyers</Button></a>
		</div>
	</CardContent>
</Card>
