<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		eyebrow = '',
		title = '',
		subtitle = '',
		contextLabel = '',
		contextValue = '',
		contextDetail = '',
		children
	}: {
		eyebrow?: string;
		title?: string;
		subtitle?: string;
		contextLabel?: string;
		contextValue?: string;
		contextDetail?: string;
		children?: Snippet;
	} = $props();
</script>

<header class="sci-page-header">
	<div class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
		<div class="min-w-0 flex-1">
			{#if eyebrow}
				<p class="sci-eyebrow">{eyebrow}</p>
			{/if}
			<h1 class="sci-page-title">{title}</h1>
			{#if subtitle}
				<p class="sci-page-subtitle">{subtitle}</p>
			{/if}
		</div>

		{#if children}
			<div class="flex shrink-0 flex-wrap gap-3 xl:justify-end">
				{@render children?.()}
			</div>
		{/if}
	</div>

	{#if contextValue || contextDetail}
		<div class="mt-2 max-w-xl rounded-xl border border-border bg-card px-4 py-4 shadow-sm">
			{#if contextLabel}
				<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-muted-foreground uppercase">
					{contextLabel}
				</p>
			{/if}
			{#if contextValue}
				<p class="mt-2 text-sm font-semibold text-foreground">{contextValue}</p>
			{/if}
			{#if contextDetail}
				<p class="mt-1 text-sm text-muted-foreground">{contextDetail}</p>
			{/if}
		</div>
	{/if}
</header>
