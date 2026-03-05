<script lang="ts">
	import { onMount } from 'svelte';
	import {
		createBien,
		fetchBiens,
		fetchScis,
		type Bien,
		type BienCreatePayload,
		type SCIOverview
	} from '$lib/api';
	import BienForm from '$lib/components/BienForm.svelte';
	import BienTable from '$lib/components/BienTable.svelte';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import { calculateBienMetrics } from '$lib/high-value/biens';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let biens: Bien[] = [];
	let scis: SCIOverview[] = [];
	let activeSciId = '';
	let loading = true;
	let submitting = false;
	let errorMessage = '';

	$: resolvedActiveSciId =
		activeSciId && scis.some((sci) => String(sci.id) === activeSciId)
			? activeSciId
			: String(scis[0]?.id || '');
	$: activeSci = scis.find((sci) => String(sci.id) === resolvedActiveSciId) ?? null;
	$: if (resolvedActiveSciId) {
		setStoredActiveSciId(resolvedActiveSciId);
	}
	$: scopedBiens = activeSci
		? biens.filter((bien) => String(bien.id_sci || '') === String(activeSci.id))
		: biens;
	$: metrics = calculateBienMetrics(scopedBiens);

	onMount(loadBiens);

	async function loadBiens() {
		loading = true;
		errorMessage = '';
		try {
			const [nextBiens, nextScis] = await Promise.all([fetchBiens(), fetchScis()]);
			biens = Array.isArray(nextBiens) ? nextBiens : [];
			scis = Array.isArray(nextScis) ? nextScis : [];
			const storedActiveSciId = getStoredActiveSciId();
			activeSciId =
				(storedActiveSciId &&
					nextScis.some((sci) => String(sci.id) === storedActiveSciId) &&
					storedActiveSciId) ||
				String(nextScis[0]?.id || '');
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de charger les biens.');
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
			errorMessage = formatApiErrorMessage(
				error,
				'Impossible d’ajouter le bien. Vérifie les champs requis.'
			);
			return false;
		} finally {
			submitting = false;
		}
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">GererSCI • Opérations</p>
		<h1 class="sci-page-title">Gestion des biens</h1>
		<p class="sci-page-subtitle">
			Centralise les actifs immobiliers de la SCI active sans exposer d’identifiants techniques dans
			les formulaires.
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

	<BienForm
		activeSciId={resolvedActiveSciId}
		activeSciLabel={activeSci?.nom || 'SCI active'}
		showSciField={!activeSci}
		{submitting}
		onSubmit={handleCreateBien}
	/>

	<BienTable biens={scopedBiens} {loading} />
</section>
