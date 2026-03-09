<script lang="ts">
	import { onMount } from 'svelte';
	import { FileText, Download } from 'lucide-svelte';
	import { fetchBiens, fetchLoyers, fetchScis, type Bien, type Loyer, type SCIOverview } from '$lib/api';
	import QuitusGenerator from '$lib/components/QuitusGenerator.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { API_URL } from '$lib/api';

	let scis = $state<SCIOverview[]>([]);
	let biens = $state<Bien[]>([]);
	let loyers = $state<Loyer[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const [s, b, l] = await Promise.all([fetchScis(), fetchBiens(), fetchLoyers()]);
			scis = s;
			biens = b;
			loyers = l;
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Documents — GererSCI</title>
	<meta name="description" content="Quittances, exports CSV et calcul fiscal." />
</svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Documents & conformité</p>
		<h1 class="sci-page-title">Centre de documents</h1>
		<p class="sci-page-subtitle">
			Quittances de loyer, exports CSV et calcul fiscal simplifié au même endroit.
		</p>
	</header>

	<div class="grid gap-6 lg:grid-cols-2">
		<div class="space-y-6">
			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="flex items-center gap-2 text-lg">
						<FileText class="h-5 w-5 text-emerald-600" />
						Quittances de loyer
					</CardTitle>
					<CardDescription>Sélectionnez un loyer pour générer la quittance PDF.</CardDescription>
				</CardHeader>
				<CardContent>
					{#if loading}
						<div class="h-32 animate-pulse rounded-2xl bg-muted"></div>
					{:else if loyers.length === 0}
						<EmptyState
							icon={FileText}
							title="Aucun loyer enregistré"
							description="Enregistrez votre premier loyer pour pouvoir générer des quittances."
							actions={[{ label: 'Ajouter un loyer', href: '/loyers' }]}
						/>
					{:else}
						<QuitusGenerator {loyers} {biens} sciName={scis[0]?.nom || ''} />
					{/if}
				</CardContent>
			</Card>
		</div>

		<div class="space-y-6">
			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="flex items-center gap-2 text-lg">
						<Download class="h-5 w-5 text-blue-600" />
						Exports de données
					</CardTitle>
					<CardDescription>Téléchargez vos données en format CSV.</CardDescription>
				</CardHeader>
				<CardContent class="space-y-3">
					<a href="{API_URL}/api/v1/export/loyers/csv" class="block">
						<Button variant="outline" class="w-full justify-start gap-2">
							<Download class="h-4 w-4" />
							Exporter les loyers (CSV)
						</Button>
					</a>
					<a href="{API_URL}/api/v1/export/biens/csv" class="block">
						<Button variant="outline" class="w-full justify-start gap-2">
							<Download class="h-4 w-4" />
							Exporter les biens (CSV)
						</Button>
					</a>
				</CardContent>
			</Card>

			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="flex items-center gap-2 text-lg">
						<FileText class="h-5 w-5 text-amber-600" />
						Calcul fiscal simplifié
					</CardTitle>
					<CardDescription>
						Résultat foncier (revenus − charges). Ne remplace pas le CERFA officiel.
					</CardDescription>
				</CardHeader>
				<CardContent>
					<p class="text-sm text-muted-foreground">
						Le calcul fiscal simplifié est disponible depuis le dashboard de chaque SCI.
						La génération PDF CERFA 2044 est accessible via l'endpoint <code>/api/v1/cerfa/2044/pdf</code>.
					</p>
					<p class="mt-2 text-xs text-muted-foreground">
						CERFA 2072 et exports fiscaux avancés en préparation.
					</p>
				</CardContent>
			</Card>
		</div>
	</div>
</section>
