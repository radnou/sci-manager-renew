<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		eyebrow = '',
		title = '',
		description = '',
		children,
		aside
	}: {
		eyebrow?: string;
		title?: string;
		description?: string;
		children?: Snippet;
		aside?: Snippet;
	} = $props();
</script>

<div class="sci-page-toolbar">
	<section class="sci-page-toolbar-main">
		{#if eyebrow}
			<p class="sci-eyebrow">{eyebrow}</p>
		{/if}
		{#if title}
			<h2 class="sci-subsection-title">{title}</h2>
		{/if}
		{#if description}
			<p class="sci-subsection-copy">{description}</p>
		{/if}
		<div class="mt-5">
			{@render children?.()}
		</div>
	</section>

	{#if aside}
		<aside class="sci-page-toolbar-aside">
			{@render aside?.()}
		</aside>
	{/if}
</div>
