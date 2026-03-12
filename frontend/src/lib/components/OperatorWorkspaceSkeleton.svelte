<script lang="ts">
	let {
		eyebrow = 'Chargement',
		title = 'Préparation de votre espace',
		description = 'Chargement des données…',
		showRail = false
	}: {
		eyebrow?: string;
		title?: string;
		description?: string;
		showRail?: boolean;
	} = $props();
</script>

<section
	class="rounded-[2rem] border border-slate-200 bg-white/92 p-6 shadow-[0_24px_70px_-42px_rgba(15,23,42,0.45)] dark:border-slate-800 dark:bg-slate-950/88"
	aria-live="polite"
>
	<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">{eyebrow}</p>
	<h2 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
	<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{description}</p>

	<div class={`mt-6 grid gap-6 ${showRail ? 'xl:grid-cols-[1.6fr_1fr]' : ''}`}>
		<div class="space-y-6">
			<div class="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
				<div class="h-4 w-32 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></div>
				<div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
					{#each Array.from({ length: 6 }) as _, index (index)}
						<div class="h-12 animate-pulse rounded-xl bg-slate-200 dark:bg-slate-800"></div>
					{/each}
				</div>
				<div class="mt-5 flex justify-end">
					<div class="h-11 w-40 animate-pulse rounded-full bg-slate-200 dark:bg-slate-800"></div>
				</div>
			</div>

			<div class="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
				<div class="flex items-end justify-between gap-4">
					<div class="space-y-2">
						<div class="h-4 w-36 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></div>
						<div class="h-3 w-56 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></div>
					</div>
					<div class="h-3 w-20 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></div>
				</div>
				<div class="mt-5 space-y-3">
					{#each Array.from({ length: 5 }) as _, index (index)}
						<div class="h-12 animate-pulse rounded-xl bg-white dark:bg-slate-950"></div>
					{/each}
				</div>
			</div>
		</div>

		{#if showRail}
			<div class="space-y-6">
				<div class="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900">
					<div class="h-4 w-28 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></div>
					<div class="mt-4 space-y-3">
						{#each Array.from({ length: 4 }) as _, index (index)}
							<div class="h-20 animate-pulse rounded-2xl bg-white dark:bg-slate-950"></div>
						{/each}
					</div>
				</div>
			</div>
		{/if}
	</div>
</section>
