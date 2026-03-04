<script lang="ts">
	import { onMount } from 'svelte';
	import { createBien, fetchBiens, type Bien, type BienCreatePayload } from '$lib/api';
	import BienForm from '$lib/components/BienForm.svelte';
	import BienTable from '$lib/components/BienTable.svelte';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import { calculateBienMetrics } from '$lib/high-value/biens';

	let biens: Bien[] = [];
	let loading = true;
	let submitting = false;
	let errorMessage = '';

	$: metrics = calculateBienMetrics(biens);

	onMount(loadBiens);

	async function loadBiens() {
		loading = true;
		errorMessage = '';
		try {
			const data = await fetchBiens();
			biens = Array.isArray(data) ? data : [];
		} catch (error) {
			errorMessage = toErrorMessage(error, 'Impossible de charger les biens.');
		} finally {
			loading = false;
		}
	}

	async function handleCreateBien(payload: BienCreatePayload): Promise<boolean> {
		submitting = true;
		errorMessage = '';

		try {
			const created = await createBien(payload);
			biens = [created, ...biens];
			return true;
		} catch (error) {
			errorMessage = toErrorMessage(error, 'Impossible d’ajouter le bien. Vérifie les champs requis.');
			return false;
		} finally {
			submitting = false;
		}
	}

	function toErrorMessage(error: unknown, fallback: string) {
		if (error instanceof Error && error.message.trim().length > 0) {
			return error.message;
		}
		return fallback;
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">SCI Manager • Opérations</p>
		<h1 class="sci-page-title">Gestion des biens</h1>
		<p class="sci-page-subtitle">
			Centralise les actifs immobiliers, les loyers et les charges pour garder une vision financière claire du
			parc SCI.
		</p>
	</header>

	<div class="grid gap-4 md:grid-cols-3">
		<KpiCard
			label="Biens actifs"
			value={metrics.count}
			caption="portefeuille total"
			trend="up"
			trendValue={metrics.count > 0 ? '+1 ce mois' : 'démarrage'}
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Loyer mensuel"
			value={metrics.totalMonthlyRentLabel}
			caption="loyer charges comprises"
			trend="up"
			trendValue="projection"
			tone="success"
			{loading}
		/>
		<KpiCard
			label="Charges mensuelles"
			value={metrics.totalChargesLabel}
			caption="charges récurrentes"
			trend="neutral"
			trendValue="contrôle"
			tone="default"
			{loading}
		/>
	</div>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	<BienForm submitting={submitting} onSubmit={handleCreateBien} />

	<BienTable {biens} {loading} />
</section>
