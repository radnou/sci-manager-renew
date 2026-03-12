<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	onMount(() => {
		goto('/#pricing', { replaceState: true });
	});
</script>

<svelte:head>
	<title>Tarifs — GererSCI</title>
	<meta name="description" content="Comparez les offres GererSCI : Essentiel (gratuit), Gestion (19€/mois) et Fiscal (39€/mois)." />
</svelte:head>

<section class="flex min-h-[50vh] items-center justify-center">
	<p class="text-sm text-slate-500 dark:text-slate-400">Redirection vers les tarifs...</p>
</section>
