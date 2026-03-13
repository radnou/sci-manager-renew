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
		<div class="mt-2 max-w-xl rounded-[1.35rem] border border-slate-200/80 bg-white/88 px-4 py-4 shadow-[0_16px_40px_-34px_rgba(15,23,42,0.6)] backdrop-blur-sm dark:border-slate-800/90 dark:bg-slate-900/78">
			{#if contextLabel}
				<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500 dark:text-slate-400">
					{contextLabel}
				</p>
			{/if}
			{#if contextValue}
				<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{contextValue}</p>
			{/if}
			{#if contextDetail}
				<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{contextDetail}</p>
			{/if}
		</div>
	{/if}
</header>
