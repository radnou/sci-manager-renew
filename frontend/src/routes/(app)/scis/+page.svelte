<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Building2, Plus } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { fetchScis, type SCIOverview } from '$lib/api';

	let scis = $state<SCIOverview[]>([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			scis = await fetchScis();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Erreur de chargement';
		} finally {
			loading = false;
		}
	});
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Gestion</p>
		<div class="flex items-center justify-between">
			<h1 class="sci-page-title">Mes SCI</h1>
			<Button onclick={() => goto('/scis')} size="sm">
				<Plus class="mr-1 h-4 w-4" /> Nouvelle SCI
			</Button>
		</div>
	</header>

	{#if loading}
		<div class="flex justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900"></div>
		</div>
	{:else if error}
		<p class="text-sm text-rose-600">{error}</p>
	{:else if scis.length === 0}
		<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-16 dark:border-slate-700">
			<Building2 class="h-10 w-10 text-slate-400" />
			<p class="mt-3 text-sm text-slate-500">Aucune SCI. Créez votre première SCI.</p>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each scis as sci (String(sci.id))}
				<a
					href="/scis/{sci.id}"
					class="group rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700"
				>
					<div class="flex items-start justify-between">
						<div>
							<h3 class="font-semibold text-slate-900 dark:text-slate-100">{sci.nom}</h3>
							{#if sci.siren}
								<p class="mt-1 text-xs text-slate-500">SIREN: {sci.siren}</p>
							{/if}
						</div>
						{#if sci.regime_fiscal}
							<span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-400">
								{sci.regime_fiscal}
							</span>
						{/if}
					</div>
					<div class="mt-4 flex gap-4 text-xs text-slate-500">
						<span>{sci.biens_count ?? 0} biens</span>
						<span>{sci.associes_count ?? 0} associés</span>
					</div>
				</a>
			{/each}
		</div>
	{/if}
</section>
