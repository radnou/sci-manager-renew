<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchBiens, fetchLoyers, type Bien, type Loyer } from '$lib/api';
	import BienTable from '$lib/components/BienTable.svelte';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import LoyerTable from '$lib/components/LoyerTable.svelte';
	import QuitusGenerator from '$lib/components/QuitusGenerator.svelte';
	import { calculateBienMetrics } from '$lib/high-value/biens';
	import { calculateLoyerMetrics } from '$lib/high-value/loyers';

	let biens: Bien[] = [];
	let loyers: Loyer[] = [];
	let loading = true;
	let errorMessage = '';

	$: bienMetrics = calculateBienMetrics(biens);
	$: loyerMetrics = calculateLoyerMetrics(loyers);
	$: activeAssets = biens.filter((bien) => (bien.statut ?? '').toLowerCase() !== 'vacant').length;

	onMount(loadOverview);

	async function loadOverview() {
		loading = true;
		errorMessage = '';
		try {
			const [nextBiens, nextLoyers] = await Promise.all([fetchBiens(), fetchLoyers()]);
			biens = Array.isArray(nextBiens) ? nextBiens : [];
			loyers = Array.isArray(nextLoyers) ? nextLoyers : [];
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Impossible de charger le tableau de bord.';
		} finally {
			loading = false;
		}
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">SCI Manager • Executive cockpit</p>
		<h1 class="sci-page-title">Tableau de bord opérationnel</h1>
		<p class="sci-page-subtitle">
			Vue consolidée des actifs, revenus locatifs et documents comptables pour piloter la performance de la SCI.
		</p>
	</header>

	<div class="grid gap-4 md:grid-cols-3">
		<KpiCard
			label="Actifs suivis"
			value={bienMetrics.count}
			caption={`${activeAssets} actifs en production`}
			trend="up"
			trendValue="portefeuille"
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Potentiel mensuel"
			value={bienMetrics.totalMonthlyRentLabel}
			caption="loyer théorique"
			trend="up"
			trendValue="projection"
			tone="success"
			{loading}
		/>
		<KpiCard
			label="Encaissements saisis"
			value={loyerMetrics.totalCollectedLabel}
			caption="journal loyers"
			trend="neutral"
			trendValue="finance"
			tone="default"
			{loading}
		/>
	</div>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	<div class="grid gap-6 xl:grid-cols-[2fr_1fr]">
		<BienTable
			biens={biens.slice(0, 6)}
			{loading}
			title="Biens stratégiques"
			description="Top des actifs affichés pour revue hebdomadaire."
		/>
		<QuitusGenerator />
	</div>

	<LoyerTable
		loyers={loyers.slice(0, 8)}
		{loading}
		title="Derniers mouvements de loyers"
		description="Historique consolidé pour contrôle des encaissements."
	/>
</section>
