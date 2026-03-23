<script lang="ts">
	type PlanRevenue = {
		plan: string;
		count: number;
		mrr: number;
		percentage: number;
	};
	type RevenueData = {
		breakdown: PlanRevenue[];
		total_mrr: number;
		arpu: number;
	};

	let { data }: { data: RevenueData } = $props();

	const planColors: Record<string, string> = {
		free: 'bg-slate-300 dark:bg-slate-600',
		gestion: 'bg-blue-500',
		pilotage: 'bg-purple-500',
		fondateur: 'bg-amber-500',
		cabinet: 'bg-emerald-500',
		starter: 'bg-blue-400',
		pro: 'bg-purple-400',
		lifetime: 'bg-amber-400'
	};

	const planLabels: Record<string, string> = {
		free: 'Free',
		gestion: 'Gestion',
		pilotage: 'Pilotage',
		fondateur: 'Fondateur',
		cabinet: 'Cabinet',
		starter: 'Starter (legacy)',
		pro: 'Pro (legacy)',
		lifetime: 'Lifetime (legacy)'
	};
</script>

<div
	class="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900"
>
	<div class="mb-4 flex items-center justify-between">
		<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Revenue Breakdown</h3>
		<div class="text-right">
			<div class="text-2xl font-bold text-slate-900 dark:text-slate-100">
				{data.total_mrr.toFixed(0)}€
			</div>
			<div class="text-xs text-slate-500">MRR</div>
		</div>
	</div>

	<!-- ARPU -->
	<div class="mb-4 rounded-lg bg-slate-50 px-4 py-3 dark:bg-slate-800">
		<span class="text-sm text-slate-500">ARPU</span>
		<span class="ml-2 text-lg font-semibold text-slate-900 dark:text-slate-100"
			>{data.arpu.toFixed(2)}€</span
		>
		<span class="text-xs text-slate-400">/user/mois</span>
	</div>

	<!-- Stacked bar -->
	<div class="mb-4 flex h-8 overflow-hidden rounded-full">
		{#each data.breakdown.filter((p) => p.percentage > 0) as plan}
			<div
				class="{planColors[plan.plan] || 'bg-slate-400'} transition-all"
				style="width: {Math.max(plan.percentage, 2)}%"
				title="{planLabels[plan.plan] || plan.plan}: {plan.mrr.toFixed(
					0
				)}€ ({plan.percentage.toFixed(1)}%)"
			></div>
		{/each}
	</div>

	<!-- Legend -->
	<div class="grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
		{#each data.breakdown as plan}
			<div class="flex items-center gap-2">
				<div class="h-3 w-3 rounded-full {planColors[plan.plan] || 'bg-slate-400'}"></div>
				<span class="text-slate-600 dark:text-slate-400">{planLabels[plan.plan] || plan.plan}</span>
				<span class="ml-auto font-medium text-slate-900 dark:text-slate-100">{plan.count}</span>
			</div>
		{/each}
	</div>
</div>
