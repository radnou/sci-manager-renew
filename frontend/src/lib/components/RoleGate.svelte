<script lang="ts">
	import { getContext } from 'svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
		fallback?: Snippet;
	}

	let { children, fallback }: Props = $props();
	const userRole = getContext<string>('userRole');
	const isGerant = userRole === 'gerant';
</script>

{#if isGerant}
	{@render children()}
{:else if fallback}
	{@render fallback()}
{/if}
