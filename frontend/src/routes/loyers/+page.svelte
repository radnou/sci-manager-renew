<script lang="ts">
	import { onMount } from 'svelte';
	import {
		createLoyer,
		deleteLoyer,
		fetchBiens,
		fetchLocataires,
		fetchLoyers,
		fetchScis,
		updateLoyer,
		type Bien,
		type Locataire,
		type Loyer,
		type LoyerCreatePayload,
		type LoyerStatus,
		type LoyerUpdatePayload,
		type SCIOverview
	} from '$lib/api';
	import EntityDrawer from '$lib/components/EntityDrawer.svelte';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import LoyerForm from '$lib/components/LoyerForm.svelte';
	import LoyerTable from '$lib/components/LoyerTable.svelte';
	import OperatorWorkspaceSkeleton from '$lib/components/OperatorWorkspaceSkeleton.svelte';
	import WorkspaceActionBar from '$lib/components/WorkspaceActionBar.svelte';
	import WorkspaceHeader from '$lib/components/WorkspaceHeader.svelte';
	import WorkspaceRailCard from '$lib/components/WorkspaceRailCard.svelte';
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
	import { buildLoyerUpdatePayload, calculateLoyerMetrics } from '$lib/high-value/loyers';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let biens: Bien[] = [];
	let locataires: Locataire[] = [];
	let loyers: Loyer[] = [];
	let scis: SCIOverview[] = [];
	let activeSciId = '';
	let loading = true;
	let submitting = false;
	let deleting = false;
	let errorMessage = '';
	let editingLoyer: Loyer | null = null;
	let loyerPendingDelete: Loyer | null = null;
	let createDialogOpen = false;
	let editDialogOpen = false;
	let deleteDialogOpen = false;
	let editLoyerDraft: {
		idBien: string;
		idLocataire: string;
		dateLoyer: string;
		montant: string;
		statut: LoyerStatus;
	} = {
		idBien: '',
		idLocataire: '',
		dateLoyer: '',
		montant: '',
		statut: 'paye'
	};

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
	$: scopedLocataires = activeSci
		? locataires.filter((locataire) => String(locataire.id_sci || '') === String(activeSci.id))
		: locataires;
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
	$: busyLoyerId = deleting
		? String(loyerPendingDelete?.id || '')
		: submitting && editingLoyer
			? String(editingLoyer.id || '')
			: '';
	$: if (!editDialogOpen) {
		editingLoyer = null;
	}
	$: if (!deleteDialogOpen) {
		loyerPendingDelete = null;
	}

	onMount(loadLoyers);

	function resolveBienLabel(idBien: Loyer['id_bien']) {
		const bien = biens.find((entry) => String(entry.id || '') === String(idBien || ''));
		if (!bien) {
			return 'Bien non identifié';
		}

		return bien.ville ? `${bien.adresse} - ${bien.ville}` : bien.adresse;
	}

	async function loadLoyers() {
		loading = true;
		errorMessage = '';
		try {
			const [nextBiens, nextLocataires, nextLoyers, nextScis] = await Promise.all([
				fetchBiens(),
				fetchLocataires(),
				fetchLoyers(),
				fetchScis()
			]);
			biens = Array.isArray(nextBiens) ? nextBiens : [];
			locataires = Array.isArray(nextLocataires) ? nextLocataires : [];
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

	async function handleCreateLoyer(
		payload: LoyerCreatePayload | LoyerUpdatePayload
	): Promise<boolean> {
		submitting = true;
		errorMessage = '';

		try {
			const created = await createLoyer(payload as LoyerCreatePayload);
			loyers = [created, ...loyers];
			createDialogOpen = false;
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

	function openEditLoyer(loyer: Loyer) {
		editingLoyer = loyer;
		editLoyerDraft = {
			idBien: String(loyer.id_bien || ''),
			idLocataire: String(loyer.id_locataire || ''),
			dateLoyer: loyer.date_loyer || '',
			montant: loyer.montant != null ? String(loyer.montant) : '',
			statut: (loyer.statut as 'paye' | 'en_attente' | 'en_retard') || 'paye'
		};
		editDialogOpen = true;
		errorMessage = '';
	}

	function closeEditLoyer() {
		editDialogOpen = false;
	}

	function openDeleteLoyer(loyer: Loyer) {
		loyerPendingDelete = loyer;
		deleteDialogOpen = true;
		errorMessage = '';
	}

	function closeDeleteLoyer() {
		deleteDialogOpen = false;
	}

	async function handleUpdateLoyer(): Promise<boolean> {
		if (!editingLoyer?.id) {
			return false;
		}

		const payload = buildLoyerUpdatePayload(editLoyerDraft);
		if (!payload) {
			errorMessage = 'Complète les champs requis avant d’enregistrer les modifications.';
			return false;
		}

		submitting = true;
		errorMessage = '';

		try {
			const updated = await updateLoyer(editingLoyer.id, payload as LoyerUpdatePayload);
			loyers = loyers.map((loyer) =>
				String(loyer.id || '') === String(updated.id || '') ? updated : loyer
			);
			closeEditLoyer();
			return true;
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de modifier le loyer sélectionné.');
			return false;
		} finally {
			submitting = false;
		}
	}

	async function handleDeleteLoyer() {
		if (!loyerPendingDelete?.id) {
			return;
		}

		deleting = true;
		errorMessage = '';

		try {
			await deleteLoyer(loyerPendingDelete.id);
			loyers = loyers.filter(
				(loyer) => String(loyer.id || '') !== String(loyerPendingDelete?.id || '')
			);
			closeDeleteLoyer();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de supprimer le loyer sélectionné.');
		} finally {
			deleting = false;
		}
	}
</script>

<svelte:head>
	<title>Loyers — GererSCI</title>
	<meta name="description" content="Suivi des encaissements et quittances de loyer." />
</svelte:head>

<section class="sci-page-shell">
	<WorkspaceHeader
		eyebrow="Exploitation • encaissements locatifs"
		title="Suivi des loyers"
		subtitle="Le journal des encaissements reste la lecture centrale. La saisie et la correction s’ouvrent à la demande dans un panneau latéral."
		contextLabel="SCI active"
		contextValue={activeSci?.nom || 'Aucune SCI sélectionnée'}
		contextDetail={activeSci
			? `${scopedLoyers.length} flux • ${scopedBiens.length} bien(s) • ${scopedLocataires.length} locataire(s)`
			: 'Choisis une SCI active pour cadrer le journal et la saisie.'}
	>
		{#if scis.length > 0}
			<label class="sci-field min-w-[14rem]">
				<span class="sci-field-label">SCI active</span>
				<select bind:value={activeSciId} class="sci-select" aria-label="SCI active">
					{#each scis as sci (sci.id)}
						<option value={String(sci.id || '')}>{sci.nom}</option>
					{/each}
				</select>
			</label>
		{/if}
	</WorkspaceHeader>

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

	{#if loading}
		<OperatorWorkspaceSkeleton
			eyebrow="Chargement revenus"
			title="Préparation du module Loyers"
			description="On aligne la SCI active, les biens rattachés et le journal locatif."
			showRail={true}
		/>
	{:else}
		<WorkspaceActionBar
			eyebrow="Cadre revenus"
			title="Journal d’encaissement avant saisie"
			description="Le flux locatif suit toujours la même séquence: bien, locataire, date, montant, statut, puis quittance. La saisie s’ouvre sans interrompre la lecture."
		>
			<div class="sci-action-grid">
				<div class="sci-action-card">
					<p class="sci-action-card-title">SCI active</p>
					<p class="sci-action-card-value">{activeSci?.nom || 'Aucune SCI sélectionnée'}</p>
					<p class="sci-action-card-body">Les encaissements affichés et saisis sont toujours filtrés sur cette SCI.</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Entités requises</p>
					<p class="sci-action-card-value">Bien, locataire, date, montant, statut</p>
					<p class="sci-action-card-body">Le loyer s’appuie désormais sur un locataire référencé, pas sur un texte libre.</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Étape suivante</p>
					<p class="sci-action-card-value">{scopedLoyers.length > 0 ? 'Contrôler puis documenter' : 'Saisir le premier flux'}</p>
					<p class="sci-action-card-body">La quittance devient une conséquence du journal, pas un écran parallèle.</p>
				</div>
			</div>
			<div class="mt-5 sci-primary-actions">
				<Button
					disabled={!activeSci || scopedBiens.length === 0 || scopedLocataires.length === 0}
					onclick={() => {
						createDialogOpen = true;
					}}
				>
					Saisir un loyer
				</Button>
				<a href="/locataires"><Button variant="outline">Ouvrir Locataires</Button></a>
				<a href="/finance"><Button variant="outline">Ouvrir Finance</Button></a>
			</div>
			{#snippet aside()}
				<WorkspaceRailCard
					title="Vision"
					description="Le journal est l’écran récurrent. Les actions de création et de correction viennent se greffer autour."
				>
					<div class="space-y-3">
						<div class="sci-action-card">
							<p class="sci-action-card-title">Maintenant</p>
							<p class="sci-action-card-value">
								{scopedBiens.length === 0
									? 'Ajouter le premier bien'
									: scopedLocataires.length === 0
										? 'Documenter le premier locataire'
										: 'Saisir le premier loyer'}
							</p>
							<p class="sci-action-card-body">L’ordre d’exploitation reste bien → locataire → loyer.</p>
						</div>
						<Button href="/biens" variant="outline" class="w-full justify-start">Vérifier les biens</Button>
					</div>
				</WorkspaceRailCard>
			{/snippet}
		</WorkspaceActionBar>

		{#if scopedBiens.length === 0}
			<p class="sci-inline-alert">
				Ajoute d'abord un bien dans le module Biens avant de saisir un loyer.
			</p>
		{:else if scopedLocataires.length === 0}
			<p class="sci-inline-alert">
				Ajoute d'abord un locataire dans le module Locataires avant de saisir un loyer.
			</p>
		{/if}

		<LoyerTable
			loyers={scopedLoyers}
			biens={scopedBiens}
			{loading}
			onEdit={openEditLoyer}
			onDelete={openDeleteLoyer}
			busyRowId={busyLoyerId}
			actionDisabled={deleting}
		/>
	{/if}

	<EntityDrawer
		bind:open={createDialogOpen}
		title="Ajouter un loyer"
		description="Crée un flux locatif complet pour la SCI active sans quitter la lecture du journal."
		size="xl"
	>
			{#if !activeSci}
				<p class="sci-inline-alert sci-inline-alert-error">
					Sélectionne d’abord une SCI active avant de saisir un loyer.
				</p>
			{:else if scopedBiens.length === 0}
				<p class="sci-inline-alert sci-inline-alert-error">
					Ajoute d’abord un bien dans le module Biens avant de saisir un loyer.
				</p>
			{:else if scopedLocataires.length === 0}
				<p class="sci-inline-alert sci-inline-alert-error">
					Ajoute d’abord un locataire dans le module Locataires avant de saisir un loyer.
				</p>
			{:else}
				<LoyerForm
					biens={scopedBiens}
					locataires={scopedLocataires}
					{submitting}
					onSubmit={handleCreateLoyer}
				/>
			{/if}
	</EntityDrawer>

	<EntityDrawer
		bind:open={editDialogOpen}
		title="Modifier le loyer"
		description="Ajuste la date, le montant ou le statut du flux sélectionné."
		size="lg"
	>
			{#if editingLoyer}
				<div class="grid gap-4 md:grid-cols-2">
					<div class="sci-field md:col-span-2">
						<span class="sci-field-label">Bien concerné</span>
						<div
							class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
						>
							{resolveBienLabel(editingLoyer.id_bien)}
						</div>
					</div>
					<label class="sci-field">
						<span class="sci-field-label">Date</span>
						<Input id="loyer-edit-date" bind:value={editLoyerDraft.dateLoyer} type="date" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Montant (€)</span>
						<Input bind:value={editLoyerDraft.montant} type="number" min="0" step="10" />
					</label>
					<label class="sci-field md:col-span-2">
						<span class="sci-field-label">Statut</span>
						<select id="loyer-edit-statut" bind:value={editLoyerDraft.statut} class="sci-select">
							<option value="paye">Payé</option>
							<option value="en_attente">En attente</option>
							<option value="en_retard">En retard</option>
						</select>
					</label>
				</div>
			{/if}
		{#snippet footer()}
			<div class="flex justify-end gap-3">
				<Button type="button" variant="outline" onclick={closeEditLoyer}>Annuler</Button>
				<Button type="button" disabled={submitting} onclick={handleUpdateLoyer}>
					{submitting ? 'Enregistrement...' : 'Enregistrer les modifications'}
				</Button>
			</div>
		{/snippet}
	</EntityDrawer>

	<Dialog.Dialog bind:open={deleteDialogOpen}>
		<Dialog.DialogContent class="sm:max-w-md">
			<Dialog.DialogHeader>
				<Dialog.DialogTitle>Supprimer le loyer</Dialog.DialogTitle>
				<Dialog.DialogDescription>
					Cette action retire définitivement la ligne du journal des loyers.
				</Dialog.DialogDescription>
			</Dialog.DialogHeader>
			<p class="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
				{#if loyerPendingDelete}
					Confirme la suppression du flux du <strong>{loyerPendingDelete.date_loyer}</strong>.
				{:else}
					Confirme la suppression du loyer sélectionné.
				{/if}
			</p>
			<Dialog.DialogFooter>
				<Button type="button" variant="outline" onclick={closeDeleteLoyer}>Annuler</Button>
				<Button type="button" variant="destructive" disabled={deleting} onclick={handleDeleteLoyer}>
					{deleting ? 'Suppression...' : 'Confirmer la suppression'}
				</Button>
			</Dialog.DialogFooter>
		</Dialog.DialogContent>
	</Dialog.Dialog>
</section>
