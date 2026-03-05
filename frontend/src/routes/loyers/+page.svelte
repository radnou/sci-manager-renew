<script lang="ts">
	import { onMount } from 'svelte';
	import {
		createLoyer,
		fetchBiens,
		fetchLoyers,
		fetchScis,
		type Bien,
		type Loyer,
		type LoyerCreatePayload,
		type SCIOverview
	} from '$lib/api';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import LoyerForm from '$lib/components/LoyerForm.svelte';
	import LoyerTable from '$lib/components/LoyerTable.svelte';
	import { calculateLoyerMetrics } from '$lib/high-value/loyers';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let biens: Bien[] = [];
	let loyers: Loyer[] = [];
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
	$: scopedLoyers = activeSci
		? loyers.filter((loyer) => {
				if (loyer.id_sci) {
					return String(loyer.id_sci) === String(activeSci.id);
				}

				const bien = biens.find((entry) => String(entry.id || '') === String(loyer.id_bien || ''));
				return String(bien?.id_sci || '') === String(activeSci.id);
			})
		: loyers;
	$: metrics = calculateLoyerMetrics(scopedLoyers);

	onMount(loadLoyers);

	async function loadLoyers() {
		loading = true;
		errorMessage = '';
		try {
			const [nextBiens, nextLoyers, nextScis] = await Promise.all([
				fetchBiens(),
				fetchLoyers(),
				fetchScis()
			]);
			biens = Array.isArray(nextBiens) ? nextBiens : [];
			loyers = Array.isArray(nextLoyers) ? nextLoyers : [];
			scis = Array.isArray(nextScis) ? nextScis : [];
			const storedActiveSciId = getStoredActiveSciId();
			activeSciId =
				(storedActiveSciId &&
					nextScis.some((sci) => String(sci.id) === storedActiveSciId) &&
					storedActiveSciId) ||
				String(nextScis[0]?.id || '');
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de charger les loyers.');
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
			errorMessage = formatApiErrorMessage(
				error,
				'Impossible d’ajouter le loyer. Vérifie les données du formulaire.'
			);
			return false;
		} finally {
			submitting = false;
		}
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">GererSCI • Revenus</p>
		<h1 class="sci-page-title">Suivi des loyers</h1>
		<p class="sci-page-subtitle">
			Pilote les encaissements mensuels de la SCI active avec des libellés métier, pas des
			identifiants bruts.
		</p>
	</header>

	<div class="grid gap-4 md:grid-cols-3">
		<KpiCard
			label="Flux encaissés"
			value={metrics.totalPaidLabel}
			caption="loyers réellement au statut payé"
			trend={metrics.totalOutstanding > 0 ? 'neutral' : 'up'}
			trendValue={metrics.totalOutstanding > 0 ? 'à suivre' : 'sécurisé'}
			tone={metrics.totalOutstanding > 0 ? 'accent' : 'success'}
			{loading}
		/>
		<KpiCard
			label="Ticket moyen"
			value={metrics.averageRecordedLabel}
			caption="montant moyen par ligne"
			trend="neutral"
			trendValue="stable"
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Retards"
			value={metrics.lateCount}
			caption="lignes au statut en retard"
			trend={metrics.lateCount > 0 ? 'down' : 'up'}
			trendValue={metrics.lateCount > 0 ? 'à traiter' : 'RAS'}
			tone={metrics.lateCount > 0 ? 'warning' : 'default'}
			{loading}
		/>
	</div>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	{#if !loading && scopedBiens.length === 0}
		<p class="sci-inline-alert">
			Ajoute d'abord un bien dans le module Biens avant de saisir un loyer.
		</p>
	{/if}

	<LoyerForm biens={scopedBiens} {submitting} onSubmit={handleCreateLoyer} />

	<LoyerTable loyers={scopedLoyers} biens={scopedBiens} {loading} />
</section>
