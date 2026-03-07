<script lang="ts">
	import { Button } from '$lib/components/ui/button';

	let {
		eyebrow = 'Espace en attente',
		title = 'Aucune donnée exploitable pour le moment',
		description = '',
		primaryHref = '',
		primaryLabel = '',
		secondaryHref = '',
		secondaryLabel = ''
	}: {
		eyebrow?: string;
		title?: string;
		description?: string;
		primaryHref?: string;
		primaryLabel?: string;
		secondaryHref?: string;
		secondaryLabel?: string;
	} = $props();
</script>

<div class="sci-empty-state text-left">
	<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500 dark:text-slate-400">
		{eyebrow}
	</p>
	<h2 class="mt-3 text-lg font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
	{#if description}
		<p class="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500 dark:text-slate-400">
			{description}
		</p>
	{/if}
	{#if primaryHref || secondaryHref}
		<div class="mt-5 flex flex-wrap gap-3">
			{#if primaryHref && primaryLabel}
				<Button href={primaryHref}>{primaryLabel}</Button>
			{/if}
			{#if secondaryHref && secondaryLabel}
				<Button href={secondaryHref} variant="outline">{secondaryLabel}</Button>
			{/if}
		</div>
	{/if}
</div>
