<script lang="ts">
	import { onMount } from 'svelte';
	import {
		createFiscalite,
		deleteFiscalite,
		fetchFiscalite,
		fetchScis,
		fetchSubscriptionEntitlements,
		updateFiscalite,
		type Fiscalite,
		type FiscaliteCreatePayload,
		type FiscaliteUpdatePayload,
		type SCIOverview,
		type SubscriptionEntitlements
	} from '$lib/api';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import OperatorWorkspaceSkeleton from '$lib/components/OperatorWorkspaceSkeleton.svelte';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Input } from '$lib/components/ui/input';
	import { calculateFiscaliteMetrics } from '$lib/high-value/fiscalite';
	import { formatEur } from '$lib/high-value/formatters';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let exercices = $state<Fiscalite[]>([]);
	let scis = $state<SCIOverview[]>([]);
	let subscription = $state<SubscriptionEntitlements | null>(null);
	let activeSciId = $state('');
	let loading = $state(true);
	let featureDisabled = $state(false);
	let submitting = $state(false);
	let deleting = $state(false);
	let errorMessage = $state('');
	let editDialogOpen = $state(false);
	let deleteDialogOpen = $state(false);
	let editingExercice = $state<Fiscalite | null>(null);
	let exercicePendingDelete = $state<Fiscalite | null>(null);

	let currentYear = new Date().getFullYear();
	let createDraft = $state({
		annee: String(currentYear),
		totalRevenus: '',
		totalCharges: ''
	});

	let editDraft = $state({
		annee: '',
		totalRevenus: '',
		totalCharges: ''
	});

	let resolvedActiveSciId = $derived(
		activeSciId && scis.some((sci) => String(sci.id) === activeSciId)
			? activeSciId
			: String(scis[0]?.id || '')
	);
	let activeSci = $derived(scis.find((sci) => String(sci.id) === resolvedActiveSciId) ?? null);
	$effect(() => {
		if (resolvedActiveSciId) {
			setStoredActiveSciId(resolvedActiveSciId);
		}
	});
	let scopedExercices = $derived(
		activeSci
			? exercices
					.filter((exercice) => String(exercice.id_sci || '') === String(activeSci.id))
					.sort((left, right) => Number(right.annee || 0) - Number(left.annee || 0))
			: exercices
	);
	let metrics = $derived(calculateFiscaliteMetrics(scopedExercices));
	let createResultPreview = $derived(
		Number(createDraft.totalRevenus || 0) - Number(createDraft.totalCharges || 0)
	);
	let editResultPreview = $derived(
		Number(editDraft.totalRevenus || 0) - Number(editDraft.totalCharges || 0)
	);
	let busyExerciceId = $derived(
		deleting
			? String(exercicePendingDelete?.id || '')
			: submitting && editingExercice
				? String(editingExercice.id || '')
				: ''
	);
	$effect(() => {
		if (!editDialogOpen) {
			editingExercice = null;
		}
	});
	$effect(() => {
		if (!deleteDialogOpen) {
			exercicePendingDelete = null;
		}
	});

	onMount(loadFiscalite);

	async function loadFiscalite() {
		loading = true;
		errorMessage = '';
		try {
			const [nextScis, nextSubscription] = await Promise.all([
				fetchScis(),
				fetchSubscriptionEntitlements()
			]);
			scis = Array.isArray(nextScis) ? nextScis : [];
			subscription = nextSubscription;
			featureDisabled = !Boolean(nextSubscription.features?.fiscalite_enabled);
			const storedActiveSciId = getStoredActiveSciId();
			activeSciId =
				(storedActiveSciId &&
					nextScis.some((sci) => String(sci.id) === storedActiveSciId) &&
					storedActiveSciId) ||
				String(nextScis[0]?.id || '');

			if (!featureDisabled) {
				const nextExercices = await fetchFiscalite();
				exercices = Array.isArray(nextExercices) ? nextExercices : [];
			} else {
				exercices = [];
			}
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de charger la fiscalité.');
		} finally {
			loading = false;
		}
	}

	function buildCreatePayload(): FiscaliteCreatePayload | null {
		if (!activeSci?.id || !createDraft.annee || !createDraft.totalRevenus || !createDraft.totalCharges) {
			return null;
		}

		return {
			id_sci: activeSci.id,
			annee: Number(createDraft.annee),
			total_revenus: Number(createDraft.totalRevenus),
			total_charges: Number(createDraft.totalCharges)
		};
	}

	function buildUpdatePayload(): FiscaliteUpdatePayload | null {
		if (!editDraft.annee || !editDraft.totalRevenus || !editDraft.totalCharges) {
			return null;
		}

		return {
			annee: Number(editDraft.annee),
			total_revenus: Number(editDraft.totalRevenus),
			total_charges: Number(editDraft.totalCharges)
		};
	}

	function resetCreateDraft() {
		createDraft = {
			annee: String(new Date().getFullYear()),
			totalRevenus: '',
			totalCharges: ''
		};
	}

	async function handleCreateExercice() {
		const payload = buildCreatePayload();
		if (!payload) {
			errorMessage = 'Complète l’année, les revenus et les charges avant de créer l’exercice.';
			return;
		}

		submitting = true;
		errorMessage = '';
		try {
			const created = await createFiscalite(payload);
			exercices = [created, ...exercices];
			resetCreateDraft();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, "Impossible d'ajouter l'exercice fiscal.");
		} finally {
			submitting = false;
		}
	}

	function openEditExercice(exercice: Fiscalite) {
		editingExercice = exercice;
		editDraft = {
			annee: String(exercice.annee || ''),
			totalRevenus: exercice.total_revenus != null ? String(exercice.total_revenus) : '',
			totalCharges: exercice.total_charges != null ? String(exercice.total_charges) : ''
		};
		editDialogOpen = true;
		errorMessage = '';
	}

	function closeEditExercice() {
		editDialogOpen = false;
	}

	async function handleUpdateExercice() {
		if (!editingExercice?.id) {
			return;
		}

		const payload = buildUpdatePayload();
		if (!payload) {
			errorMessage = 'Complète l’année, les revenus et les charges avant d’enregistrer les modifications.';
			return;
		}

		submitting = true;
		errorMessage = '';
		try {
			const updated = await updateFiscalite(editingExercice.id, payload);
			exercices = exercices.map((exercice) =>
				String(exercice.id || '') === String(updated.id || '') ? updated : exercice
			);
			closeEditExercice();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, "Impossible de modifier l'exercice sélectionné.");
		} finally {
			submitting = false;
		}
	}

	function openDeleteExercice(exercice: Fiscalite) {
		exercicePendingDelete = exercice;
		deleteDialogOpen = true;
		errorMessage = '';
	}

	function closeDeleteExercice() {
		deleteDialogOpen = false;
	}

	async function handleDeleteExercice() {
		if (!exercicePendingDelete?.id) {
			return;
		}

		deleting = true;
		errorMessage = '';
		try {
			await deleteFiscalite(exercicePendingDelete.id);
			exercices = exercices.filter(
				(exercice) => String(exercice.id || '') !== String(exercicePendingDelete?.id || '')
			);
			closeDeleteExercice();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, "Impossible de supprimer l'exercice sélectionné.");
		} finally {
			deleting = false;
		}
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">GererSCI • Fiscalité</p>
		<h1 class="sci-page-title">Clôture fiscale</h1>
		<p class="sci-page-subtitle">
			Consolide les exercices de la SCI active avec une lecture annuelle des revenus, des charges et
			du résultat fiscal exploitable en arbitrage.
		</p>
		{#if scis.length > 0}
			<div class="mt-5 max-w-sm">
				<label class="sci-field">
					<span class="sci-field-label">SCI active</span>
					<select bind:value={activeSciId} class="sci-select" aria-label="SCI active">
						{#each scis as sci (sci.id)}
							<option value={String(sci.id || '')}>{sci.nom}</option>
						{/each}
					</select>
				</label>
			</div>
		{/if}
	</header>

	<div class="grid gap-4 md:grid-cols-3">
		<KpiCard
			label="Exercices consolidés"
			value={metrics.count}
			caption="historique fiscal"
			trend={metrics.count > 0 ? 'up' : 'neutral'}
			trendValue={metrics.count > 0 ? 'documenté' : 'à démarrer'}
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Dernier exercice"
			value={metrics.latestYear ?? 'N/A'}
			caption={`résultat ${metrics.latestResultLabel}`}
			trend={metrics.latestYear ? 'up' : 'neutral'}
			trendValue={metrics.latestYear ? 'clos' : 'à préparer'}
			tone="success"
			{loading}
		/>
		<KpiCard
			label="Résultat cumulé"
			value={metrics.totalResultLabel}
			caption="somme des exercices suivis"
			trend="neutral"
			trendValue="vision"
			tone="default"
			{loading}
		/>
	</div>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	{#if loading}
		<OperatorWorkspaceSkeleton
			eyebrow="Chargement fiscalité"
			title="Préparation du module fiscal"
			description="On aligne la SCI active, les capacités d’offre et les exercices consolidés."
		/>
	{:else if featureDisabled}
		<div class="rounded-[1.75rem] border border-slate-200 bg-white/92 p-6 shadow-[0_20px_65px_-45px_rgba(15,23,42,0.5)] dark:border-slate-800 dark:bg-slate-900/84">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Fonctionnalité d’offre</p>
			<h2 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">La fiscalité consolidée n’est pas active sur cette offre</h2>
			<p class="mt-2 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
				Le module de clôture fiscale est réservé aux offres qui couvrent les arbitrages annuels et la
				documentation d’exercice.
			</p>
			<div class="mt-5 flex flex-wrap gap-3">
				<a href="/account"><Button>Voir mon offre</Button></a>
				<a href="/pricing"><Button variant="outline">Comparer les offres</Button></a>
			</div>
		</div>
	{:else if !activeSci}
		<div class="rounded-[1.75rem] border border-slate-200 bg-white/92 p-6 shadow-[0_20px_65px_-45px_rgba(15,23,42,0.5)] dark:border-slate-800 dark:bg-slate-900/84">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Pré-requis métier</p>
			<h2 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">Sélectionne une SCI active</h2>
			<p class="mt-2 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
				La clôture fiscale s’opère toujours dans le contexte d’une SCI précise. Choisis d’abord la société
				cible avant de renseigner l’exercice.
			</p>
			<div class="mt-5 flex flex-wrap gap-3">
				<a href="/scis"><Button>Ouvrir le portefeuille SCI</Button></a>
				<a href="/dashboard"><Button variant="outline">Retour au cockpit</Button></a>
			</div>
		</div>
	{:else}
		<Card class="sci-section-card">
			<CardHeader>
				<CardTitle class="text-lg">Parcours opérateur</CardTitle>
				<CardDescription>
					La fiscalité consolidée agrège les revenus et les charges déjà documentés sur la SCI active.
					Elle ne remplace pas les pièces, elle structure l’arbitrage.
				</CardDescription>
			</CardHeader>
			<CardContent class="grid gap-3 pt-0 md:grid-cols-3">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">SCI active</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{activeSci.nom}</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Régime {activeSci.regime_fiscal || 'N/A'} • l’exercice fiscal se lit sur cette société.
					</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Caractéristiques</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						Année, revenus, charges, résultat calculé
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Le résultat fiscal est calculé automatiquement pour garder une lecture cohérente.
					</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Étape suivante</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{scopedExercices.length > 0 ? 'Comparer avec les charges' : 'Créer le premier exercice'}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Le module Charges reste la source terrain des dépenses; ici, tu consolides et arbitres.
					</p>
					<div class="mt-4">
						<a href="/charges"><Button size="sm" variant="outline">Ouvrir Charges</Button></a>
					</div>
				</div>
			</CardContent>
		</Card>

		<div class="grid gap-6 xl:grid-cols-[1.05fr_1.4fr]">
			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="text-lg">Nouvel exercice fiscal</CardTitle>
					<CardDescription>
						Saisis l’année et les agrégats de revenus/charges de la SCI active.
					</CardDescription>
				</CardHeader>
				<CardContent class="grid gap-4 pt-0">
					<label class="sci-field">
						<span class="sci-field-label">Année</span>
						<Input bind:value={createDraft.annee} type="number" min="2000" max="2100" />
					</label>
					<div class="grid gap-4 md:grid-cols-2">
						<label class="sci-field">
							<span class="sci-field-label">Total revenus (€)</span>
							<Input bind:value={createDraft.totalRevenus} type="number" min="0" step="100" />
						</label>
						<label class="sci-field">
							<span class="sci-field-label">Total charges (€)</span>
							<Input bind:value={createDraft.totalCharges} type="number" min="0" step="100" />
						</label>
					</div>
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
						<p class="font-semibold text-slate-900 dark:text-slate-100">
							Résultat fiscal projeté: {formatEur(createResultPreview, '0 €')}
						</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							Le résultat est recalculé automatiquement à partir des revenus et des charges.
						</p>
					</div>
					<div class="flex justify-end">
						<Button disabled={submitting} onclick={handleCreateExercice}>
							{submitting ? 'Création...' : 'Ajouter l’exercice'}
						</Button>
					</div>
				</CardContent>
			</Card>

			<Card class="sci-section-card">
				<CardHeader>
					<div class="flex items-end justify-between gap-4">
						<div>
							<CardTitle class="text-lg">Historique fiscal</CardTitle>
							<CardDescription>
								Exercices consolidés de la SCI active, triés du plus récent au plus ancien.
							</CardDescription>
						</div>
						<p class="text-[0.72rem] font-semibold tracking-[0.2em] uppercase text-slate-500">
							{scopedExercices.length} enregistrement{scopedExercices.length > 1 ? 's' : ''}
						</p>
					</div>
				</CardHeader>
				<CardContent class="grid gap-3 pt-0">
					{#if scopedExercices.length === 0}
						<div class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
							Aucun exercice fiscal consolidé pour l’instant sur la SCI active.
						</div>
					{:else}
						{#each scopedExercices as exercice (String(exercice.id))}
							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<div class="flex flex-wrap items-start justify-between gap-3">
									<div>
										<div class="flex flex-wrap items-center gap-2">
											<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
												Exercice {exercice.annee}
											</p>
											<span class="rounded-full bg-slate-200 px-2.5 py-1 text-[11px] font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
												Régime {exercice.regime_fiscal || activeSci.regime_fiscal || 'N/A'}
											</span>
										</div>
										<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
											Revenus {formatEur(exercice.total_revenus, 'N/A')} • Charges {formatEur(exercice.total_charges, 'N/A')}
										</p>
									</div>
									<div class="text-right">
										<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Résultat</p>
										<p class="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">
											{formatEur(exercice.resultat_fiscal, 'N/A')}
										</p>
									</div>
								</div>
								<div class="mt-4 flex flex-wrap justify-end gap-2">
									<Button
										size="sm"
										variant="outline"
										onclick={() => openEditExercice(exercice)}
										disabled={submitting || deleting}
									>
										Modifier
									</Button>
									<Button
										size="sm"
										variant="outline"
										onclick={() => openDeleteExercice(exercice)}
										disabled={submitting || deleting || busyExerciceId === String(exercice.id || '')}
									>
										Supprimer
									</Button>
								</div>
							</div>
						{/each}
					{/if}
				</CardContent>
			</Card>
		</div>
	{/if}

	<Dialog.Dialog bind:open={editDialogOpen}>
		<Dialog.Content class="sm:max-w-[36rem]">
			<Dialog.Header>
				<Dialog.Title>Modifier l’exercice fiscal</Dialog.Title>
				<Dialog.Description>
					Mets à jour l’année ou les agrégats de revenus/charges. Le résultat fiscal sera recalculé.
				</Dialog.Description>
			</Dialog.Header>
			<div class="grid gap-4 py-2">
				<label class="sci-field">
					<span class="sci-field-label">Année</span>
					<Input bind:value={editDraft.annee} type="number" min="2000" max="2100" />
				</label>
				<div class="grid gap-4 md:grid-cols-2">
					<label class="sci-field">
						<span class="sci-field-label">Total revenus (€)</span>
						<Input bind:value={editDraft.totalRevenus} type="number" min="0" step="100" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Total charges (€)</span>
						<Input bind:value={editDraft.totalCharges} type="number" min="0" step="100" />
					</label>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
					<p class="font-semibold text-slate-900 dark:text-slate-100">
						Résultat fiscal recalculé: {formatEur(editResultPreview, '0 €')}
					</p>
				</div>
			</div>
			<Dialog.Footer>
				<Button variant="outline" onclick={closeEditExercice}>Annuler</Button>
				<Button disabled={submitting} onclick={handleUpdateExercice}>
					{submitting ? 'Enregistrement...' : 'Enregistrer les modifications'}
				</Button>
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Dialog>

	<Dialog.Dialog bind:open={deleteDialogOpen}>
		<Dialog.Content class="sm:max-w-[32rem]">
			<Dialog.Header>
				<Dialog.Title>Supprimer cet exercice ?</Dialog.Title>
				<Dialog.Description>
					Cette action retire l’exercice consolidé du module fiscal de la SCI active.
				</Dialog.Description>
			</Dialog.Header>
			<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
				<p class="font-semibold text-slate-900 dark:text-slate-100">
					Exercice {exercicePendingDelete?.annee}
				</p>
				<p class="mt-1 text-slate-500 dark:text-slate-400">
					Résultat {formatEur(exercicePendingDelete?.resultat_fiscal, 'N/A')}
				</p>
			</div>
			<Dialog.Footer>
				<Button variant="outline" onclick={closeDeleteExercice}>Annuler</Button>
				<Button disabled={deleting} onclick={handleDeleteExercice}>
					{deleting ? 'Suppression...' : 'Confirmer la suppression'}
				</Button>
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Dialog>
</section>
