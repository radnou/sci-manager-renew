<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	onMount(() => {
		goto('/confidentialite', { replaceState: true });
	});
</script>

<svelte:head>
	<title>RGPD — GérerSCI</title>
	<meta name="robots" content="noindex, follow" />
	<link rel="canonical" href="https://gerersci.fr/confidentialite" />
	<meta http-equiv="refresh" content="0; url=/confidentialite" />
</svelte:head>

<section class="flex min-h-[60vh] items-center justify-center">
	<p class="text-sm text-slate-500 dark:text-slate-400">
		Redirection vers <a href="/confidentialite" class="underline">la page Confidentialité (RGPD)</a>…
	</p>
</section>
