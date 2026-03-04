<script lang="ts">
	import { onMount } from 'svelte';
	import { createLoyer, fetchLoyers, type Loyer, type LoyerCreatePayload } from '$lib/api';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import LoyerForm from '$lib/components/LoyerForm.svelte';
	import LoyerTable from '$lib/components/LoyerTable.svelte';
	import { calculateLoyerMetrics } from '$lib/high-value/loyers';

	let loyers: Loyer[] = [];
	let loading = true;
	let submitting = false;
	let errorMessage = '';

	$: metrics = calculateLoyerMetrics(loyers);

	onMount(loadLoyers);

	async function loadLoyers() {
		loading = true;
		errorMessage = '';
		try {
			const data = await fetchLoyers();
			loyers = Array.isArray(data) ? data : [];
		} catch (error) {
			errorMessage = toErrorMessage(error, 'Impossible de charger les loyers.');
		} finally {
			loading = false;
		}
	}

	async function handleCreateLoyer(payload: LoyerCreatePayload): Promise<boolean> {
		submitting = true;
		errorMessage = '';

		try {
			const created = await createLoyer(payload);
			loyers = [created, ...loyers];
			return true;
		} catch (error) {
			errorMessage = toErrorMessage(error, 'Impossible d’ajouter le loyer. Vérifie les données du formulaire.');
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
		<p class="sci-eyebrow">SCI Manager • Revenus</p>
		<h1 class="sci-page-title">Suivi des loyers</h1>
		<p class="sci-page-subtitle">
			Pilote les encaissements mensuels, détecte les retards et fiabilise les flux de trésorerie de la SCI.
		</p>
	</header>

	<div class="grid gap-4 md:grid-cols-3">
		<KpiCard
			label="Encaissements"
			value={metrics.totalCollectedLabel}
			caption="sur la période affichée"
			trend="up"
			trendValue="+4.8%"
			tone="success"
			{loading}
		/>
		<KpiCard
			label="Ticket moyen"
			value={metrics.averageCollectedLabel}
			caption="montant moyen par ligne"
			trend="neutral"
			trendValue="stable"
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Retards"
			value={metrics.lateCount}
			caption="lignes au statut retard"
			trend={metrics.lateCount > 0 ? 'down' : 'up'}
			trendValue={metrics.lateCount > 0 ? 'à traiter' : 'RAS'}
			tone={metrics.lateCount > 0 ? 'warning' : 'default'}
			{loading}
		/>
	</div>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	<LoyerForm submitting={submitting} onSubmit={handleCreateLoyer} />

	<LoyerTable {loyers} {loading} />
</section>
