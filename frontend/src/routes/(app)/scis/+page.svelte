<script lang="ts">
	import { onMount } from 'svelte';
	import { Building2, Plus, Landmark } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { fetchScis, type SCIOverview } from '$lib/api';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import SciModal from '$lib/components/fiche-bien/modals/SciModal.svelte';

	let showSciModal = $state(false);
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

<svelte:head><title>Portefeuille | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Gestion</p>
		<div class="flex items-center justify-between">
			<h1 class="sci-page-title">Mes SCI</h1>
			<Button onclick={() => showSciModal = true} size="sm">
				<Plus class="mr-1 h-4 w-4" /> Nouvelle SCI
			</Button>
		</div>
	</header>

	{#if loading}
		<div class="sci-loading" aria-label="Chargement"></div>
	{:else if error}
		<p class="text-sm text-rose-600">{error}</p>
	{:else if scis.length === 0}
		<EmptyState
			icon={Landmark}
			title="Bienvenue dans votre espace SCI"
			description="Commencez par créer votre première Société Civile Immobilière. Vous pourrez ensuite y rattacher vos biens, associés et documents."
			ctaText="Créer ma première SCI"
			ctaHref="/onboarding"
		/>
	{:else}
		<div class="sci-stagger grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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

	<SciModal bind:open={showSciModal} />
</section>
