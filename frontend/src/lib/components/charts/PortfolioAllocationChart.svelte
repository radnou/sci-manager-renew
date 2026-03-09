<script lang="ts">
	import type { Bien, SCIOverview } from '$lib/api';

	interface Props {
		biens: Bien[];
		scis: SCIOverview[];
	}

	let { biens, scis }: Props = $props();

	const allocationBySci = $derived(() => {
		const grouped = new Map<string, { name: string; count: number; rent: number }>();
		for (const sci of scis) {
			grouped.set(String(sci.id), { name: sci.nom, count: 0, rent: 0 });
		}
		for (const bien of biens) {
			const sciId = String(bien.id_sci || '');
			const entry = grouped.get(sciId);
			if (entry) {
				entry.count++;
				entry.rent += bien.loyer_cc ?? 0;
			}
		}
		return Array.from(grouped.values()).filter((e) => e.count > 0);
	});

	const data = $derived(allocationBySci());
	const totalRent = $derived(data.reduce((sum, d) => sum + d.rent, 0));

	const colors = ['bg-blue-500', 'bg-emerald-500', 'bg-amber-500', 'bg-rose-500', 'bg-purple-500', 'bg-cyan-500'];
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
	<p class="mb-3 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
		Répartition du portefeuille
	</p>

	{#if data.length === 0}
		<div class="flex h-32 items-center justify-center text-sm text-slate-400 dark:text-slate-500">
			Aucun bien documenté
		</div>
	{:else}
		<!-- Horizontal stacked bar -->
		<div class="mb-3 flex h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
			{#each data as entry, i}
				{@const width = totalRent > 0 ? (entry.rent / totalRent) * 100 : 100 / data.length}
				<div
					class="{colors[i % colors.length]} transition-all duration-500"
					style="width: {width}%"
					title="{entry.name}: {entry.count} biens, {entry.rent}€/mois"
				></div>
			{/each}
		</div>

		<div class="space-y-2">
			{#each data as entry, i}
				<div class="flex items-center justify-between text-sm">
					<div class="flex items-center gap-2">
						<div class="h-2.5 w-2.5 rounded-full {colors[i % colors.length]}"></div>
						<span class="text-slate-700 dark:text-slate-300">{entry.name}</span>
					</div>
					<div class="text-right">
						<span class="font-medium text-slate-900 dark:text-slate-100">{entry.count} biens</span>
						<span class="ml-2 text-xs text-slate-500">{entry.rent}€/mois</span>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
