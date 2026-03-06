<script lang="ts">
	import { onMount } from 'svelte';
	import {
		createBien,
		deleteBien,
		fetchBiens,
		fetchScis,
		fetchSubscriptionEntitlements,
		updateBien,
		type Bien,
		type BienCreatePayload,
		type BienType,
		type BienUpdatePayload,
		type SCIOverview,
		type SubscriptionEntitlements
	} from '$lib/api';
	import BienForm from '$lib/components/BienForm.svelte';
	import BienTable from '$lib/components/BienTable.svelte';
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
	import { buildBienUpdatePayload, calculateBienMetrics } from '$lib/high-value/biens';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let biens: Bien[] = [];
	let scis: SCIOverview[] = [];
	let activeSciId = '';
	let loading = true;
	let submitting = false;
	let deleting = false;
	let errorMessage = '';
	let subscription: SubscriptionEntitlements | null = null;
	let editingBien: Bien | null = null;
	let bienPendingDelete: Bien | null = null;
	let editDialogOpen = false;
	let deleteDialogOpen = false;
	let editBienDraft: {
		idSci: string;
		adresse: string;
		ville: string;
		codePostal: string;
		typeLocatif: BienType;
		loyerCC: string;
		charges: string;
		tmi: string;
		acquisitionDate: string;
		prixAcquisition: string;
	} = {
		idSci: '',
		adresse: '',
		ville: '',
		codePostal: '',
		typeLocatif: 'nu',
		loyerCC: '',
		charges: '',
		tmi: '',
		acquisitionDate: '',
		prixAcquisition: ''
	};

	$: resolvedActiveSciId =
		activeSciId && scis.some((sci) => String(sci.id) === activeSciId)
			? activeSciId
			: String(scis[0]?.id || '');
	$: activeSci = scis.find((sci) => String(sci.id) === resolvedActiveSciId) ?? null;
	$: bienCreationDisabled =
		Boolean(subscription) &&
		subscription?.max_biens != null &&
		subscription.current_biens >= subscription.max_biens;
	$: bienCreationDisabledMessage = bienCreationDisabled
		? "Le quota de biens de l'offre active est atteint. Passe à une offre supérieure pour continuer."
		: '';
	$: if (resolvedActiveSciId) {
		setStoredActiveSciId(resolvedActiveSciId);
	}
	$: scopedBiens = activeSci
		? biens.filter((bien) => String(bien.id_sci || '') === String(activeSci.id))
		: biens;
	$: metrics = calculateBienMetrics(scopedBiens);
	$: busyBienId = deleting
		? String(bienPendingDelete?.id || '')
		: submitting && editingBien
			? String(editingBien.id || '')
			: '';
	$: if (!editDialogOpen) {
		editingBien = null;
	}
	$: if (!deleteDialogOpen) {
		bienPendingDelete = null;
	}

	onMount(loadBiens);

	async function loadBiens() {
		loading = true;
		errorMessage = '';
		try {
			const [nextBiens, nextScis, nextSubscription] = await Promise.all([
				fetchBiens(),
				fetchScis(),
				fetchSubscriptionEntitlements()
			]);
			biens = Array.isArray(nextBiens) ? nextBiens : [];
			scis = Array.isArray(nextScis) ? nextScis : [];
			subscription = nextSubscription;
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

	async function handleCreateBien(
		payload: BienCreatePayload | BienUpdatePayload
	): Promise<boolean> {
		submitting = true;
		errorMessage = '';

		try {
			const created = await createBien(payload as BienCreatePayload);
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

	function openEditBien(bien: Bien) {
		editingBien = bien;
		editBienDraft = {
			idSci: String(bien.id_sci || resolvedActiveSciId),
			adresse: bien.adresse || '',
			ville: bien.ville || '',
			codePostal: bien.code_postal || '',
			typeLocatif: (bien.type_locatif as 'nu' | 'meuble' | 'mixte') || 'nu',
			loyerCC: bien.loyer_cc != null ? String(bien.loyer_cc) : '',
			charges: bien.charges != null ? String(bien.charges) : '',
			tmi: bien.tmi != null ? String(bien.tmi) : '',
			acquisitionDate: bien.acquisition_date || '',
			prixAcquisition: bien.prix_acquisition != null ? String(bien.prix_acquisition) : ''
		};
		editDialogOpen = true;
		errorMessage = '';
	}

	function closeEditBien() {
		editDialogOpen = false;
	}

	function openDeleteBien(bien: Bien) {
		bienPendingDelete = bien;
		deleteDialogOpen = true;
		errorMessage = '';
	}

	function closeDeleteBien() {
		deleteDialogOpen = false;
	}

	async function handleUpdateBien(): Promise<boolean> {
		if (!editingBien?.id) {
			return false;
		}

		const payload = buildBienUpdatePayload(editBienDraft);
		if (!payload) {
			errorMessage = 'Complète les champs requis avant d’enregistrer les modifications.';
			return false;
		}

		submitting = true;
		errorMessage = '';

		try {
			const updated = await updateBien(editingBien.id, payload as BienUpdatePayload);
			biens = biens.map((bien) =>
				String(bien.id || '') === String(updated.id || '') ? updated : bien
			);
			closeEditBien();
			return true;
		} catch (error) {
			errorMessage = formatApiErrorMessage(
				error,
				'Impossible de modifier le bien. Vérifie les données saisies.'
			);
			return false;
		} finally {
			submitting = false;
		}
	}

	async function handleDeleteBien() {
		if (!bienPendingDelete?.id) {
			return;
		}

		deleting = true;
		errorMessage = '';

		try {
			await deleteBien(bienPendingDelete.id);
			biens = biens.filter((bien) => String(bien.id || '') !== String(bienPendingDelete?.id || ''));
			closeDeleteBien();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de supprimer le bien sélectionné.');
		} finally {
			deleting = false;
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

	{#if loading}
		<OperatorWorkspaceSkeleton
			eyebrow="Chargement patrimoine"
			title="Préparation du module Biens"
			description="On récupère la SCI active, les capacités d’offre et le portefeuille immobilier."
		/>
	{:else}
		<Card class="sci-section-card">
			<CardHeader>
				<CardTitle class="text-lg">Parcours opérateur</CardTitle>
				<CardDescription>
					Ici, tu rattaches un actif à la SCI active, puis tu contrôles immédiatement le portefeuille
					affiché plus bas.
				</CardDescription>
			</CardHeader>
			<CardContent class="grid gap-3 pt-0 md:grid-cols-3">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">SCI active</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{activeSci?.nom || 'Aucune SCI sélectionnée'}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Un bien est toujours créé dans le contexte d’une SCI métier.
					</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Caractéristiques du bien</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						Adresse, type locatif, loyer CC, charges, TMI, acquisition
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Le formulaire attend une fiche complète, pas juste une adresse.
					</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Étape suivante</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{metrics.count > 0 ? 'Contrôler le portefeuille et corriger' : 'Créer le premier bien'}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Une fois le bien créé, passe à `Loyers` pour saisir le locataire et le premier flux.
					</p>
				</div>
			</CardContent>
		</Card>

		{#if activeSci}
			<BienForm
				activeSciId={resolvedActiveSciId}
				activeSciLabel={activeSci.nom}
				showSciField={false}
				{submitting}
				disabled={bienCreationDisabled}
				disabledMessage={bienCreationDisabledMessage}
				onSubmit={handleCreateBien}
			/>
		{:else}
			<div class="rounded-[1.75rem] border border-slate-200 bg-white/92 p-6 shadow-[0_20px_65px_-45px_rgba(15,23,42,0.5)] dark:border-slate-800 dark:bg-slate-900/84">
				<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Pré-requis métier</p>
				<h2 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">Sélectionne d’abord une SCI active</h2>
				<p class="mt-2 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
					Un bien doit toujours être rattaché à une SCI métier, jamais à un identifiant technique. Passe par le portefeuille SCI pour choisir ou créer la société cible.
				</p>
				<div class="mt-5 flex flex-wrap gap-3">
					<a href="/scis"><Button>Ouvrir le portefeuille SCI</Button></a>
					<a href="/dashboard"><Button variant="outline">Retour au cockpit</Button></a>
				</div>
			</div>
		{/if}

		<BienTable
			biens={scopedBiens}
			{loading}
			onEdit={openEditBien}
			onDelete={openDeleteBien}
			busyRowId={busyBienId}
			actionDisabled={deleting}
		/>
	{/if}

	<Dialog.Dialog bind:open={editDialogOpen}>
		<Dialog.DialogContent class="sm:max-w-4xl">
			<Dialog.DialogHeader>
				<Dialog.DialogTitle>Modifier le bien</Dialog.DialogTitle>
				<Dialog.DialogDescription>
					Mets à jour les informations métier du bien sélectionné sans changer la SCI de
					rattachement.
				</Dialog.DialogDescription>
			</Dialog.DialogHeader>
			{#if editingBien}
				<div class="grid gap-4 md:grid-cols-2">
					<label class="sci-field md:col-span-2">
						<span class="sci-field-label">Adresse</span>
						<Input bind:value={editBienDraft.adresse} />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Ville</span>
						<Input id="bien-edit-ville" bind:value={editBienDraft.ville} />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Code postal</span>
						<Input bind:value={editBienDraft.codePostal} inputmode="numeric" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Type locatif</span>
						<select bind:value={editBienDraft.typeLocatif} class="sci-select">
							<option value="nu">Nu</option>
							<option value="meuble">Meublé</option>
							<option value="mixte">Mixte</option>
						</select>
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Loyer CC (€)</span>
						<Input bind:value={editBienDraft.loyerCC} type="number" min="0" step="10" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Charges (€)</span>
						<Input bind:value={editBienDraft.charges} type="number" min="0" step="10" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">TMI (%)</span>
						<Input bind:value={editBienDraft.tmi} type="number" min="0" max="100" step="0.5" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Date d'acquisition</span>
						<Input bind:value={editBienDraft.acquisitionDate} type="date" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Prix acquisition (€)</span>
						<Input bind:value={editBienDraft.prixAcquisition} type="number" min="0" step="1000" />
					</label>
				</div>
				<Dialog.DialogFooter>
					<Button type="button" variant="outline" onclick={closeEditBien}>Annuler</Button>
					<Button type="button" disabled={submitting} onclick={handleUpdateBien}>
						{submitting ? 'Enregistrement...' : 'Enregistrer les modifications'}
					</Button>
				</Dialog.DialogFooter>
			{/if}
		</Dialog.DialogContent>
	</Dialog.Dialog>

	<Dialog.Dialog bind:open={deleteDialogOpen}>
		<Dialog.DialogContent class="sm:max-w-md">
			<Dialog.DialogHeader>
				<Dialog.DialogTitle>Supprimer le bien</Dialog.DialogTitle>
				<Dialog.DialogDescription>
					Cette action retire le bien du portefeuille affiché pour la SCI active.
				</Dialog.DialogDescription>
			</Dialog.DialogHeader>
			<p class="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
				{#if bienPendingDelete}
					Confirme la suppression de <strong>{bienPendingDelete.adresse}</strong>.
				{:else}
					Confirme la suppression du bien sélectionné.
				{/if}
			</p>
			<Dialog.DialogFooter>
				<Button type="button" variant="outline" onclick={closeDeleteBien}>Annuler</Button>
				<Button type="button" variant="destructive" disabled={deleting} onclick={handleDeleteBien}>
					{deleting ? 'Suppression...' : 'Confirmer la suppression'}
				</Button>
			</Dialog.DialogFooter>
		</Dialog.DialogContent>
	</Dialog.Dialog>
</section>
