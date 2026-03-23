<script lang="ts">
	type Cohort = {
		month: string;
		total: number;
		retained: number[];
	};
	type CohortData = {
		cohorts: Cohort[];
	};

	let { data }: { data: CohortData } = $props();

	function retentionColor(pct: number): string {
		if (pct >= 80) return 'bg-emerald-600 text-white';
		if (pct >= 60) return 'bg-emerald-400 text-white';
		if (pct >= 40) return 'bg-emerald-300 text-slate-900';
		if (pct >= 20) return 'bg-emerald-100 text-slate-700';
		return 'bg-slate-50 text-slate-500 dark:bg-slate-800 dark:text-slate-400';
	}

	function formatMonth(iso: string): string {
		const d = new Date(iso + '-01');
		return d.toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' });
	}

	const maxMonths = $derived(Math.max(...data.cohorts.map(c => c.retained.length), 0));
</script>

<div class="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
	<h3 class="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Rétention par cohorte</h3>

	<div class="overflow-x-auto">
		<table class="w-full text-sm">
			<thead>
				<tr>
					<th class="px-2 py-1 text-left text-xs font-medium text-slate-500">Cohorte</th>
					<th class="px-2 py-1 text-center text-xs font-medium text-slate-500">Total</th>
					{#each Array(maxMonths) as _, i}
						<th class="px-2 py-1 text-center text-xs font-medium text-slate-500">M{i}</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each data.cohorts as cohort}
					<tr>
						<td class="whitespace-nowrap px-2 py-1 font-medium text-slate-700 dark:text-slate-300">
							{formatMonth(cohort.month)}
						</td>
						<td class="px-2 py-1 text-center font-medium text-slate-900 dark:text-slate-100">
							{cohort.total}
						</td>
						{#each cohort.retained as count, i}
							{@const pct = cohort.total > 0 ? (count / cohort.total) * 100 : 0}
							<td class="px-1 py-1">
								<div class="rounded px-2 py-1 text-center text-xs font-medium {retentionColor(pct)}">
									{pct.toFixed(0)}%
								</div>
							</td>
						{/each}
						{#each Array(maxMonths - cohort.retained.length) as _}
							<td></td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
