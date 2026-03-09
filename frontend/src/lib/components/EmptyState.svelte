<script lang="ts">
	import type { Component, Snippet } from 'svelte';
	import { Button } from '$lib/components/ui/button';

	interface Props {
		icon?: any;
		title: string;
		description?: string;
		ctaText?: string;
		ctaHref?: string;
	}

	let { icon: Icon, title, description, ctaText, ctaHref }: Props = $props();
</script>

<div
	class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center dark:border-slate-700 dark:bg-slate-900"
>
	{#if Icon}
		<div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
			<Icon class="h-6 w-6 text-slate-400 dark:text-slate-500" />
		</div>
	{/if}
	<h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
	{#if description}
		<p class="mt-1.5 max-w-sm text-sm text-slate-500 dark:text-slate-400">{description}</p>
	{/if}
	{#if ctaText && ctaHref}
		<a href={ctaHref} class="mt-4">
			<Button size="sm">{ctaText}</Button>
		</a>
	{/if}
</div>
