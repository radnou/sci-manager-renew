<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	onMount(() => {
		goto('/pricing', { replaceState: true });
	});
</script>

<svelte:head>
	<title>Tarifs — GérerSCI</title>
	<meta name="robots" content="noindex, follow" />
	<link rel="canonical" href="https://gerersci.fr/pricing" />
	<meta http-equiv="refresh" content="0; url=/pricing" />
</svelte:head>

<section class="flex min-h-[60vh] items-center justify-center">
	<p class="text-sm text-slate-500 dark:text-slate-400">
		Redirection vers <a href="/pricing" class="underline">la page Tarifs</a>…
	</p>
</section>
