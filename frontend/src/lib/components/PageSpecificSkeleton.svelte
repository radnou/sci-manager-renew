<script lang="ts">
	import OperatorWorkspaceSkeleton from '$lib/components/OperatorWorkspaceSkeleton.svelte';

	let {
		eyebrow = 'Chargement',
		title = 'Préparation du workspace',
		description = 'Les données sont en cours de chargement.',
		showRail = true,
		mode = 'workspace'
	}: {
		eyebrow?: string;
		title?: string;
		description?: string;
		showRail?: boolean;
		mode?: 'workspace' | 'hub';
	} = $props();
</script>

{#if mode === 'hub'}
	<section
		class="rounded-[2rem] border border-slate-200/80 bg-white/92 p-6 shadow-[0_24px_70px_-42px_rgba(15,23,42,0.45)] backdrop-blur-sm dark:border-slate-800/90 dark:bg-slate-900/84"
		aria-live="polite"
	>
		<p class="sci-eyebrow">{eyebrow}</p>
		<h2 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
		<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{description}</p>
		<div class="mt-6 grid gap-4 lg:grid-cols-3">
			{#each Array.from({ length: 3 }) as _, index (index)}
				<div class="h-48 animate-pulse rounded-[1.5rem] bg-slate-100 dark:bg-slate-900"></div>
			{/each}
		</div>
	</section>
{:else}
	<OperatorWorkspaceSkeleton {eyebrow} {title} {description} {showRail} />
{/if}
