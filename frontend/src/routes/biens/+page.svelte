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
	import { Button } from '$lib/components/ui/button';
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

	<BienForm
		activeSciId={resolvedActiveSciId}
		activeSciLabel={activeSci?.nom || 'SCI active'}
		showSciField={!activeSci}
		{submitting}
		disabled={bienCreationDisabled}
		disabledMessage={bienCreationDisabledMessage}
		onSubmit={handleCreateBien}
	/>

	<BienTable
		biens={scopedBiens}
		{loading}
		onEdit={openEditBien}
		onDelete={openDeleteBien}
		busyRowId={busyBienId}
		actionDisabled={deleting}
	/>

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
