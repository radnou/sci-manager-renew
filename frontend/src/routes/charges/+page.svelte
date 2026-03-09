<script lang="ts">
	import { onMount } from 'svelte';
	import {
		createCharge,
		deleteCharge,
		fetchBiens,
		fetchCharges,
		fetchScis,
		fetchSubscriptionEntitlements,
		updateCharge,
		type Bien,
		type Charge,
		type ChargeCreatePayload,
		type ChargeUpdatePayload,
		type SCIOverview,
		type SubscriptionEntitlements
	} from '$lib/api';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import EntityDrawer from '$lib/components/EntityDrawer.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import KpiCard from '$lib/components/KPI-Card.svelte';
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
	import { CHARGE_TYPE_OPTIONS, calculateChargeMetrics } from '$lib/high-value/charges';
	import { formatFrDate } from '$lib/high-value/formatters';
	import { formatApiErrorMessage, mapChargeTypeLabel } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let charges = $state<Charge[]>([]);
	let biens = $state<Bien[]>([]);
	let scis = $state<SCIOverview[]>([]);
	let subscription = $state<SubscriptionEntitlements | null>(null);
	let activeSciId = $state('');
	let loading = $state(true);
	let featureDisabled = $state(false);
	let submitting = $state(false);
	let deleting = $state(false);
	let errorMessage = $state('');
	let createDialogOpen = $state(false);
	let editDialogOpen = $state(false);
	let deleteDialogOpen = $state(false);
	let editingCharge = $state<Charge | null>(null);
	let chargePendingDelete = $state<Charge | null>(null);

	let createDraft = $state({
		idBien: '',
		typeCharge: 'assurance',
		montant: '',
		datePaiement: new Date().toISOString().slice(0, 10)
	});

	let editDraft = $state({
		typeCharge: 'assurance',
		montant: '',
		datePaiement: ''
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
	let scopedBiens = $derived(
		activeSci ? biens.filter((bien) => String(bien.id_sci || '') === String(activeSci.id)) : biens
	);
	let scopedCharges = $derived(
		activeSci
			? charges.filter((charge) => String(charge.id_sci || '') === String(activeSci.id))
			: charges
	);
	let metrics = $derived(calculateChargeMetrics(scopedCharges));
	let busyChargeId = $derived(
		deleting
			? String(chargePendingDelete?.id || '')
			: submitting && editingCharge
				? String(editingCharge.id || '')
				: ''
	);
	$effect(() => {
		if (!createDraft.idBien && scopedBiens.length > 0) {
			createDraft.idBien = String(scopedBiens[0].id || '');
		}
	});
	$effect(() => {
		if (!editDialogOpen) {
			editingCharge = null;
		}
	});
	$effect(() => {
		if (!deleteDialogOpen) {
			chargePendingDelete = null;
		}
	});

	onMount(loadCharges);

	async function loadCharges() {
		loading = true;
		errorMessage = '';
		try {
			const [nextScis, nextBiens, nextSubscription] = await Promise.all([
				fetchScis(),
				fetchBiens(),
				fetchSubscriptionEntitlements()
			]);
			scis = Array.isArray(nextScis) ? nextScis : [];
			biens = Array.isArray(nextBiens) ? nextBiens : [];
			subscription = nextSubscription;
			featureDisabled = !Boolean(nextSubscription.features?.charges_enabled);
			const storedActiveSciId = getStoredActiveSciId();
			activeSciId =
				(storedActiveSciId &&
					nextScis.some((sci) => String(sci.id) === storedActiveSciId) &&
					storedActiveSciId) ||
				String(nextScis[0]?.id || '');

			if (!featureDisabled) {
				const nextCharges = await fetchCharges();
				charges = Array.isArray(nextCharges) ? nextCharges : [];
			} else {
				charges = [];
			}
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de charger les charges.');
		} finally {
			loading = false;
		}
	}

	function buildCreatePayload(): ChargeCreatePayload | null {
		if (!createDraft.idBien || !createDraft.montant || !createDraft.datePaiement) {
			return null;
		}

		return {
			id_bien: createDraft.idBien,
			type_charge: createDraft.typeCharge,
			montant: Number(createDraft.montant),
			date_paiement: createDraft.datePaiement
		};
	}

	function buildUpdatePayload(): ChargeUpdatePayload | null {
		if (!editDraft.montant || !editDraft.datePaiement) {
			return null;
		}

		return {
			type_charge: editDraft.typeCharge,
			montant: Number(editDraft.montant),
			date_paiement: editDraft.datePaiement
		};
	}

	function resetCreateDraft() {
		createDraft = {
			idBien: scopedBiens[0] ? String(scopedBiens[0].id || '') : '',
			typeCharge: 'assurance',
			montant: '',
			datePaiement: new Date().toISOString().slice(0, 10)
		};
	}

	function resolveBienLabel(charge: Charge) {
		if (charge.bien_adresse) {
			return charge.bien_ville
				? `${charge.bien_adresse} - ${charge.bien_ville}`
				: charge.bien_adresse;
		}

		const bien = biens.find((entry) => String(entry.id || '') === String(charge.id_bien || ''));
		if (!bien) {
			return 'Bien non identifié';
		}
		return bien.ville ? `${bien.adresse} - ${bien.ville}` : bien.adresse;
	}

	async function handleCreateCharge() {
		const payload = buildCreatePayload();
		if (!payload) {
			errorMessage = 'Complète le bien, le type, la date et le montant avant d’ajouter la charge.';
			return;
		}

		submitting = true;
		errorMessage = '';
		try {
			const created = await createCharge(payload);
			charges = [created, ...charges];
			resetCreateDraft();
			createDialogOpen = false;
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible d’ajouter la charge sélectionnée.');
		} finally {
			submitting = false;
		}
	}

	function openEditCharge(charge: Charge) {
		editingCharge = charge;
		editDraft = {
			typeCharge: charge.type_charge || 'assurance',
			montant: charge.montant != null ? String(charge.montant) : '',
			datePaiement: charge.date_paiement || ''
		};
		editDialogOpen = true;
		errorMessage = '';
	}

	function closeEditCharge() {
		editDialogOpen = false;
	}

	async function handleUpdateCharge() {
		if (!editingCharge?.id) {
			return;
		}

		const payload = buildUpdatePayload();
		if (!payload) {
			errorMessage =
				'Complète le type, le montant et la date avant d’enregistrer les modifications.';
			return;
		}

		submitting = true;
		errorMessage = '';
		try {
			const updated = await updateCharge(editingCharge.id, payload);
			charges = charges.map((charge) =>
				String(charge.id || '') === String(updated.id || '') ? updated : charge
			);
			closeEditCharge();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de modifier la charge sélectionnée.');
		} finally {
			submitting = false;
		}
	}

	function openDeleteCharge(charge: Charge) {
		chargePendingDelete = charge;
		deleteDialogOpen = true;
		errorMessage = '';
	}

	function closeDeleteCharge() {
		deleteDialogOpen = false;
	}

	async function handleDeleteCharge() {
		if (!chargePendingDelete?.id) {
			return;
		}

		deleting = true;
		errorMessage = '';
		try {
			await deleteCharge(chargePendingDelete.id);
			charges = charges.filter(
				(charge) => String(charge.id || '') !== String(chargePendingDelete?.id || '')
			);
			closeDeleteCharge();
		} catch (error) {
			errorMessage = formatApiErrorMessage(
				error,
				'Impossible de supprimer la charge sélectionnée.'
			);
		} finally {
			deleting = false;
		}
	}
</script>

<svelte:head>
	<title>Charges — GererSCI</title>
	<meta name="description" content="Pilotage des charges et décaissements." />
</svelte:head>

<section class="sci-page-shell">
	<WorkspaceHeader
		eyebrow="Finance • decaissements"
		title="Pilotage des charges"
		subtitle="Le journal des sorties reste la lecture principale. La creation et la correction des mouvements se font dans un panneau lateral, sans casser la lecture du registre."
		contextLabel="SCI active"
		contextValue={activeSci?.nom || 'Aucune SCI selectionnee'}
		contextDetail={activeSci
			? `${scopedCharges.length} charge(s) • ${metrics.totalLabel} documentes`
			: 'Choisis une SCI active pour rattacher les depenses au bon patrimoine.'}
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
			label="Charges documentées"
			value={metrics.count}
			caption="mouvements saisis"
			trend={metrics.count > 0 ? 'up' : 'neutral'}
			trendValue={metrics.count > 0 ? 'suivi actif' : 'à démarrer'}
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Montant total"
			value={metrics.totalLabel}
			caption="charges enregistrées"
			trend="neutral"
			trendValue="pilotage"
			tone="warning"
			{loading}
		/>
		<KpiCard
			label="Charge moyenne"
			value={metrics.averageLabel}
			caption={metrics.latestChargeDate
				? `dernière le ${formatFrDate(metrics.latestChargeDate)}`
				: 'aucun mouvement'}
			trend={metrics.latestChargeDate ? 'up' : 'neutral'}
			trendValue={metrics.latestChargeDate ? 'à jour' : 'en attente'}
			tone="default"
			{loading}
		/>
	</div>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	{#if loading}
		<OperatorWorkspaceSkeleton
			eyebrow="Chargement charges"
			title="Préparation du registre des charges"
			description="On aligne la SCI active, les biens rattachés et le journal des décaissements."
		/>
	{:else if featureDisabled}
		<div
			class="rounded-[1.75rem] border border-border bg-card p-6 shadow-[0_20px_65px_-45px_rgba(15,23,42,0.5)]"
		>
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-muted-foreground uppercase">
				Fonctionnalité d’offre
			</p>
			<h2 class="mt-3 text-2xl font-semibold text-foreground">
				Le suivi des charges n’est pas actif sur cette offre
			</h2>
			<p class="mt-2 max-w-2xl text-sm leading-7 text-muted-foreground">
				Le pilotage détaillé des charges est réservé aux offres qui incluent la dimension dépenses
				et arbitrages fiscaux.
			</p>
			<div class="mt-5 flex flex-wrap gap-3">
				<a href="/account"><Button>Voir mon offre</Button></a>
				<a href="/settings"><Button variant="outline">Revenir aux préférences</Button></a>
			</div>
		</div>
	{:else if !activeSci}
		<EmptyState
			align="left"
			eyebrow="Pre-requis metier"
			title="Selectionne une SCI active"
			description="Chaque charge doit etre rattachee a un bien et donc a une SCI identifiee. Passe d’abord par le portefeuille SCI."
			actions={[
				{ label: 'Ouvrir le portefeuille SCI', href: '/scis' },
				{ label: 'Retour au cockpit', href: '/dashboard', variant: 'outline' }
			]}
		/>
	{:else}
		<WorkspaceActionBar
			eyebrow="Cadre charges"
			title="Journal des sorties avant cloture"
			description="Une charge utile au pilotage fiscal est toujours rattachee a un bien de la SCI active, a un type metier clair et a une date de paiement verifiable."
		>
			<div class="sci-action-grid">
				<div class="sci-action-card">
					<p class="sci-action-card-title">SCI active</p>
					<p class="sci-action-card-value">{activeSci.nom}</p>
					<p class="sci-action-card-body">
						Les charges saisies ici alimentent la lecture operationnelle de cette SCI.
					</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Caracteristiques</p>
					<p class="sci-action-card-value">Bien, type, montant, date de paiement</p>
					<p class="sci-action-card-body">
						Le journal doit rester exploitable par bien et par exercice.
					</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Etape suivante</p>
					<p class="sci-action-card-value">
						{scopedCharges.length > 0 ? 'Preparer la fiscalite' : 'Documenter la premiere charge'}
					</p>
					<p class="sci-action-card-body">
						Une fois les charges documentees, passe en fiscalite pour consolider.
					</p>
				</div>
			</div>
			<div class="sci-primary-actions mt-5">
				<Button disabled={scopedBiens.length === 0} onclick={() => (createDialogOpen = true)}>
					Documenter une charge
				</Button>
				<a href="/fiscalite"><Button variant="outline">Ouvrir Fiscalite</Button></a>
				<a href="/biens"><Button variant="outline">Verifier les biens</Button></a>
			</div>
			{#snippet aside()}
				<WorkspaceRailCard
					title="Vision"
					description="Le journal de charges est frequent. La creation et la correction restent des actions de contexte."
				>
					<div class="space-y-3">
						<div class="sci-action-card">
							<p class="sci-action-card-title">Maintenant</p>
							<p class="sci-action-card-value">
								{scopedBiens.length === 0
									? 'Ajouter le premier bien'
									: scopedCharges.length === 0
										? 'Documenter la premiere charge'
										: 'Passer a la cloture'}
							</p>
							<p class="sci-action-card-body">
								Le journal doit preceder l’exercice fiscal consolide.
							</p>
						</div>
						<Button href="/finance" variant="outline" class="w-full justify-start"
							>Ouvrir le hub Finance</Button
						>
					</div>
				</WorkspaceRailCard>
			{/snippet}
		</WorkspaceActionBar>

		{#if scopedBiens.length === 0}
			<EmptyState
				align="left"
				eyebrow="Pre-requis patrimoine"
				title="Ajoute d’abord un bien"
				description="Une charge ne peut pas etre saisie sans bien support. Rattache d’abord le premier actif a la SCI active."
				actions={[
					{ label: 'Ouvrir Biens', href: '/biens' },
					{ label: 'Retour au portefeuille SCI', href: '/scis', variant: 'outline' }
				]}
			/>
		{:else}
			<Card class="sci-section-card">
				<CardHeader>
					<div class="flex items-end justify-between gap-4">
						<div>
							<CardTitle class="text-lg">Journal des charges</CardTitle>
							<CardDescription>
								Historique des dépenses rattachées au patrimoine de la SCI active.
							</CardDescription>
						</div>
						<p
							class="text-[0.72rem] font-semibold tracking-[0.2em] text-muted-foreground uppercase"
						>
							{scopedCharges.length} enregistrement{scopedCharges.length > 1 ? 's' : ''}
						</p>
					</div>
				</CardHeader>
				<CardContent class="grid gap-3 pt-0">
					{#if scopedCharges.length === 0}
						<div
							class="rounded-2xl border border-dashed border-border bg-muted p-8 text-center text-sm text-muted-foreground"
						>
							Aucune charge documentée pour l’instant sur la SCI active.
						</div>
					{:else}
						{#each scopedCharges as charge (String(charge.id))}
							<div class="rounded-2xl border border-border bg-muted p-4">
								<div class="flex flex-wrap items-start justify-between gap-3">
									<div>
										<div class="flex flex-wrap items-center gap-2">
											<p class="text-sm font-semibold text-foreground">
												{mapChargeTypeLabel(charge.type_charge)}
											</p>
											<StatusBadge
												text={formatFrDate(charge.date_paiement)}
												variant="neutral"
												size="md"
											/>
										</div>
										<p class="mt-1 text-sm text-muted-foreground">
											{resolveBienLabel(charge)}
										</p>
									</div>
									<div class="text-right">
										<p
											class="text-[0.68rem] font-semibold tracking-[0.18em] text-muted-foreground uppercase"
										>
											Montant
										</p>
										<p class="mt-1 text-sm font-semibold text-foreground">{charge.montant} €</p>
									</div>
								</div>
								<div class="mt-4 flex flex-wrap justify-end gap-2">
									<Button
										size="sm"
										variant="outline"
										onclick={() => openEditCharge(charge)}
										disabled={submitting || deleting}
									>
										Modifier
									</Button>
									<Button
										size="sm"
										variant="outline"
										onclick={() => openDeleteCharge(charge)}
										disabled={submitting || deleting || busyChargeId === String(charge.id || '')}
									>
										Supprimer
									</Button>
								</div>
							</div>
						{/each}
					{/if}
				</CardContent>
			</Card>
		{/if}
	{/if}

	<EntityDrawer
		bind:open={createDialogOpen}
		title="Ajouter une charge"
		description="Ajoute un mouvement de depense sur un bien de la SCI active sans quitter le journal."
		size="lg"
	>
		{#if scopedBiens.length === 0}
			<p class="sci-inline-alert sci-inline-alert-error">
				Ajoute d’abord un bien à la SCI active avant de créer une charge.
			</p>
		{:else}
			<div class="grid gap-4 py-2">
				<label class="sci-field">
					<span class="sci-field-label">Bien</span>
					<select bind:value={createDraft.idBien} class="sci-select">
						{#each scopedBiens as bien (String(bien.id || ''))}
							<option value={String(bien.id || '')}>
								{bien.ville ? `${bien.adresse} - ${bien.ville}` : bien.adresse}
							</option>
						{/each}
					</select>
				</label>
				<div class="grid gap-4 md:grid-cols-2">
					<label class="sci-field">
						<span class="sci-field-label">Type de charge</span>
						<select bind:value={createDraft.typeCharge} class="sci-select">
							{#each CHARGE_TYPE_OPTIONS as typeOption (typeOption.value)}
								<option value={typeOption.value}>{typeOption.label}</option>
							{/each}
						</select>
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Montant (€)</span>
						<Input bind:value={createDraft.montant} type="number" min="1" step="10" />
					</label>
				</div>
				<label class="sci-field">
					<span class="sci-field-label">Date de paiement</span>
					<Input bind:value={createDraft.datePaiement} type="date" />
				</label>
			</div>
		{/if}
		{#snippet footer()}
			<div class="flex justify-end gap-3">
				<Button variant="outline" onclick={() => (createDialogOpen = false)}>Annuler</Button>
				<Button disabled={submitting || scopedBiens.length === 0} onclick={handleCreateCharge}>
					{submitting ? 'Creation...' : 'Ajouter la charge'}
				</Button>
			</div>
		{/snippet}
	</EntityDrawer>

	<EntityDrawer
		bind:open={editDialogOpen}
		title="Modifier la charge"
		description="Ajuste le type, le montant ou la date de paiement du mouvement selectionne."
		size="lg"
	>
		<div class="grid gap-4 py-2">
			<label class="sci-field">
				<span class="sci-field-label">Type de charge</span>
				<select bind:value={editDraft.typeCharge} class="sci-select">
					{#each CHARGE_TYPE_OPTIONS as typeOption (typeOption.value)}
						<option value={typeOption.value}>{typeOption.label}</option>
					{/each}
				</select>
			</label>
			<div class="grid gap-4 md:grid-cols-2">
				<label class="sci-field">
					<span class="sci-field-label">Montant (€)</span>
					<Input bind:value={editDraft.montant} type="number" min="1" step="10" />
				</label>
				<label class="sci-field">
					<span class="sci-field-label">Date de paiement</span>
					<Input bind:value={editDraft.datePaiement} type="date" />
				</label>
			</div>
		</div>
		{#snippet footer()}
			<div class="flex justify-end gap-3">
				<Button variant="outline" onclick={closeEditCharge}>Annuler</Button>
				<Button disabled={submitting} onclick={handleUpdateCharge}>
					{submitting ? 'Enregistrement...' : 'Enregistrer les modifications'}
				</Button>
			</div>
		{/snippet}
	</EntityDrawer>

	<Dialog.Dialog bind:open={deleteDialogOpen}>
		<Dialog.Content class="sm:max-w-[32rem]">
			<Dialog.Header>
				<Dialog.Title>Supprimer cette charge ?</Dialog.Title>
				<Dialog.Description>
					Cette action retire le mouvement du journal de charges de la SCI active.
				</Dialog.Description>
			</Dialog.Header>
			<div class="rounded-2xl border border-border bg-muted p-4 text-sm">
				<p class="font-semibold text-foreground">
					{mapChargeTypeLabel(chargePendingDelete?.type_charge)}
				</p>
				<p class="mt-1 text-muted-foreground">
					{resolveBienLabel(
						chargePendingDelete || { id_bien: '', type_charge: '', montant: 0, date_paiement: '' }
					)}
					{#if chargePendingDelete?.date_paiement}
						{' '}• {formatFrDate(chargePendingDelete.date_paiement)}
					{/if}
				</p>
			</div>
			<Dialog.Footer>
				<Button variant="outline" onclick={closeDeleteCharge}>Annuler</Button>
				<Button disabled={deleting} onclick={handleDeleteCharge}>
					{deleting ? 'Suppression...' : 'Confirmer la suppression'}
				</Button>
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Dialog>
</section>
