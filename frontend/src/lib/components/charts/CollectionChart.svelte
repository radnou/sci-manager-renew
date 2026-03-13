<script lang="ts">
	import { Chart, Bars, Axis } from 'layerchart';
	import { scaleBand } from 'd3-scale';
	import type { Loyer } from '$lib/api';

	interface Props {
		loyers: Loyer[];
	}

	let { loyers }: Props = $props();

	const monthlyData = $derived(() => {
		const grouped = new Map<string, { paid: number; total: number }>();

		for (const loyer of loyers) {
			if (!loyer.date_loyer) continue;
			const month = loyer.date_loyer.substring(0, 7); // YYYY-MM
			const existing = grouped.get(month) || { paid: 0, total: 0 };
			existing.total += loyer.montant ?? 0;
			if (loyer.statut === 'paye') existing.paid += loyer.montant ?? 0;
			grouped.set(month, existing);
		}

		return Array.from(grouped.entries())
			.sort(([a], [b]) => a.localeCompare(b))
			.slice(-6)
			.map(([month, data]) => ({
				month: month.substring(5), // MM
				rate: data.total > 0 ? Math.round((data.paid / data.total) * 100) : 0,
				paid: data.paid,
				total: data.total
			}));
	});

	const data = $derived(monthlyData());
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
	<p class="mb-3 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
		Taux de recouvrement (6 derniers mois)
	</p>

	{#if data.length === 0}
		<div class="flex h-32 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
			Pas encore de données
		</div>
	{:else}
		<div class="h-40">
			<Chart
				{data}
				x="month"
				xScale={scaleBand().padding(0.3)}
				y="rate"
				yDomain={[0, 100]}
				padding={{ left: 32, bottom: 24, top: 8, right: 8 }}
			>
				<Axis placement="left" format={(d) => `${d}%`} ticks={3} />
				<Axis placement="bottom" />
				<Bars
					radius={4}
					class="fill-blue-500 dark:fill-blue-400"
				/>
			</Chart>
		</div>
	{/if}
</div>
