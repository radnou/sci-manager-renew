<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		title = '',
		description = '',
		children
	}: {
		title?: string;
		description?: string;
		children?: Snippet;
	} = $props();
</script>

<section class="rounded-[1.35rem] border border-slate-200/80 bg-slate-50/90 p-4 dark:border-slate-700 dark:bg-slate-900/88">
	{#if title}
		<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500 dark:text-slate-400">
			{title}
		</p>
	{/if}
	{#if description}
		<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{description}</p>
	{/if}
	<div class="mt-4">
		{@render children?.()}
	</div>
</section>
