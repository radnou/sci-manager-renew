<script lang="ts">
	import { onMount } from 'svelte';
	import { Calculator, FileText, TrendingUp } from 'lucide-svelte';
	import { fetchScis, type SCIOverview } from '$lib/api';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';

	let scis = $state<SCIOverview[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			scis = await fetchScis();
		} finally {
			loading = false;
		}
	});
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Conformité & fiscalité</p>
		<h1 class="sci-page-title">Fiscalité</h1>
		<p class="sci-page-subtitle">
			Résultat foncier simplifié et génération CERFA 2044 pour vos SCI.
		</p>
	</header>

	<div class="grid gap-6 lg:grid-cols-2">
		<Card class="sci-section-card">
			<CardHeader>
				<CardTitle class="flex items-center gap-2 text-lg">
					<Calculator class="h-5 w-5 text-amber-600" />
					Résultat foncier simplifié
				</CardTitle>
				<CardDescription>
					Revenus − charges = résultat fiscal. Calcul indicatif, ne remplace pas le CERFA officiel.
				</CardDescription>
			</CardHeader>
			<CardContent>
				{#if loading}
					<div class="h-32 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
				{:else if scis.length === 0}
					<EmptyState
						title="Aucune SCI enregistrée"
						description="Créez votre première SCI pour accéder au calcul fiscal."
						ctaText="Créer une SCI"
						ctaHref="/scis"
					/>
				{:else}
					<p class="text-sm text-slate-600 dark:text-slate-300">
						Le calcul fiscal simplifié est accessible depuis le dashboard de chaque SCI.
						Sélectionnez une SCI pour consulter le détail.
					</p>
					<div class="mt-4 grid gap-2">
						{#each scis as sci (sci.id)}
							<a href="/dashboard" class="block">
								<Button variant="outline" class="w-full justify-start gap-2">
									<TrendingUp class="h-4 w-4" />
									{sci.nom}
								</Button>
							</a>
						{/each}
					</div>
				{/if}
			</CardContent>
		</Card>

		<Card class="sci-section-card">
			<CardHeader>
				<CardTitle class="flex items-center gap-2 text-lg">
					<FileText class="h-5 w-5 text-blue-600" />
					CERFA 2044
				</CardTitle>
				<CardDescription>
					Génération PDF du formulaire CERFA 2044 pour la déclaration foncière.
				</CardDescription>
			</CardHeader>
			<CardContent>
				<p class="text-sm text-slate-600 dark:text-slate-300">
					La génération PDF CERFA 2044 est disponible via l'API.
					Renseignez les revenus et charges de l'exercice pour obtenir le formulaire pré-rempli.
				</p>
				<p class="mt-3 text-xs text-slate-400 dark:text-slate-500">
					CERFA 2072 et exports fiscaux avancés prévus dans la roadmap.
				</p>
			</CardContent>
		</Card>
	</div>
</section>
