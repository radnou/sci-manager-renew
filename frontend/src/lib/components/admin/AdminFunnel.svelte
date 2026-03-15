<script lang="ts">
	type FunnelStep = { label: string; count: number; rate: number };
	type Props = { steps: FunnelStep[]; bottleneck_index: number };
	let { steps, bottleneck_index }: Props = $props();
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Funnel d'activation</h2>
	<p class="mt-1 text-xs text-slate-500">Parcours des utilisateurs de l'inscription au paiement</p>

	<div class="mt-5 space-y-3">
		{#each steps as step, i (step.label)}
			{@const isBottleneck = i === bottleneck_index && steps.length > 1}
			<div class="flex items-center gap-3">
				<div class="w-44 flex-shrink-0">
					<p class="text-sm font-medium text-slate-700 dark:text-slate-300">{step.label}</p>
				</div>
				<div class="flex flex-1 items-center gap-2">
					<div class="relative h-6 flex-1 rounded-full bg-slate-100 dark:bg-slate-800">
						<div
							class="absolute inset-y-0 left-0 rounded-full transition-all {isBottleneck
								? 'bg-amber-500'
								: 'bg-sky-500'}"
							style="width: {step.rate}%"
						></div>
					</div>
					<span class="w-10 text-right text-xs font-semibold text-slate-600 dark:text-slate-400">
						{step.count}
					</span>
					<span
						class="w-12 rounded-full px-2 py-0.5 text-center text-xs font-semibold {isBottleneck
							? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
							: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}"
					>
						{step.rate}%
					</span>
				</div>
				{#if isBottleneck}
					<span class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
						Goulot
					</span>
				{/if}
			</div>
		{/each}
	</div>
</div>
