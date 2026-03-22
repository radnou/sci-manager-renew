<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		goto('/settings#confidentialite', { replaceState: true });
	});
</script>

<svelte:head><title>Redirection... | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	<div class="flex items-center justify-center py-16">
		<div class="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900 dark:border-slate-600 dark:border-t-slate-100"></div>
		<span class="ml-3 text-sm text-slate-500 dark:text-slate-400">Redirection vers les paramètres...</span>
	</div>
</section>
