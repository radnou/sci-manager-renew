<script lang="ts">
	import { Chart, Area, Axis, Spline } from 'layerchart';
	import { scaleTime } from 'd3-scale';
	import type { Loyer } from '$lib/api';

	interface Props {
		loyers: Loyer[];
	}

	let { loyers }: Props = $props();

	const monthlyRevenue = $derived(() => {
		const grouped = new Map<string, number>();

		for (const loyer of loyers) {
			if (!loyer.date_loyer || loyer.statut !== 'paye') continue;
			const month = loyer.date_loyer.substring(0, 7);
			grouped.set(month, (grouped.get(month) || 0) + (loyer.montant ?? 0));
		}

		return Array.from(grouped.entries())
			.sort(([a], [b]) => a.localeCompare(b))
			.slice(-12)
			.map(([month, amount]) => ({
				date: new Date(`${month}-01`),
				amount
			}));
	});

	const data = $derived(monthlyRevenue());
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
	<p class="mb-3 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
		Revenus encaissés (12 mois)
	</p>

	{#if data.length < 2}
		<div class="flex h-32 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
			Pas assez de données
		</div>
	{:else}
		<div class="h-40">
			<Chart
				{data}
				x="date"
				xScale={scaleTime()}
				y="amount"
				yDomain={[0, null]}
				padding={{ left: 48, bottom: 24, top: 8, right: 8 }}
			>
				<Axis placement="left" format={(d) => `${d}€`} ticks={3} />
				<Axis placement="bottom" format={(d) => {
					const date = d instanceof Date ? d : new Date(d);
					return date.toLocaleDateString('fr-FR', { month: 'short' });
				}} ticks={4} />
				<Area class="fill-emerald-500/20 dark:fill-emerald-400/15" line={{ class: 'stroke-none' }} />
				<Spline class="stroke-emerald-500 dark:stroke-emerald-400" width={2} />
			</Chart>
		</div>
	{/if}
</div>
