<script lang="ts">
	import { onMount } from 'svelte';
	import {
		createLocataire,
		deleteLocataire,
		fetchBiens,
		fetchLocataires,
		fetchScis,
		updateLocataire,
		type Bien,
		type Locataire,
		type LocataireCreatePayload,
		type LocataireUpdatePayload,
		type SCIOverview
	} from '$lib/api';
	import EntityDrawer from '$lib/components/EntityDrawer.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
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
	import { formatFrDate } from '$lib/high-value/formatters';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let biens = $state<Bien[]>([]);
	let locataires = $state<Locataire[]>([]);
	let scis = $state<SCIOverview[]>([]);
	let activeSciId = $state('');
	let loading = $state(true);
	let submitting = $state(false);
	let deleting = $state(false);
	let errorMessage = $state('');
	let createDialogOpen = $state(false);
	let editDialogOpen = $state(false);
	let deleteDialogOpen = $state(false);
	let editingLocataire = $state<Locataire | null>(null);
	let locatairePendingDelete = $state<Locataire | null>(null);

	let createDraft = $state({
		idBien: '',
		nom: '',
		email: '',
		dateDebut: new Date().toISOString().slice(0, 10),
		dateFin: ''
	});

	let editDraft = $state({
		idBien: '',
		nom: '',
		email: '',
		dateDebut: '',
		dateFin: ''
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
		activeSci
			? biens.filter((bien) => String(bien.id_sci || '') === String(activeSci.id))
		: biens
	);
	let scopedLocataires = $derived(
		activeSci
			? locataires.filter((locataire) => String(locataire.id_sci || '') === String(activeSci.id))
		: locataires
	);
	let activeLocatairesCount = $derived(scopedLocataires.filter((locataire) => {
		const endDate = locataire.date_fin ? Date.parse(locataire.date_fin) : Number.POSITIVE_INFINITY;
		return endDate >= Date.now();
	}).length);
	let documentedEmailsCount = $derived(scopedLocataires.filter((locataire) =>
		Boolean(String(locataire.email || '').trim())
	).length);
	let busyLocataireId = $derived(
		deleting
			? String(locatairePendingDelete?.id || '')
		: submitting && editingLocataire
			? String(editingLocataire.id || '')
			: ''
	);
	$effect(() => {
		if (!createDraft.idBien && scopedBiens.length > 0) {
			createDraft.idBien = String(scopedBiens[0].id || '');
		}
	});
	$effect(() => {
		if (!editDialogOpen) {
			editingLocataire = null;
		}
	});
	$effect(() => {
		if (!deleteDialogOpen) {
			locatairePendingDelete = null;
		}
	});

	onMount(loadLocataires);

	function buildCreatePayload(): LocataireCreatePayload | null {
		if (!createDraft.idBien || !createDraft.nom.trim() || !createDraft.dateDebut) {
			return null;
		}

		return {
			id_bien: createDraft.idBien,
			nom: createDraft.nom.trim(),
			email: createDraft.email.trim() || null,
			date_debut: createDraft.dateDebut,
			date_fin: createDraft.dateFin || null
		};
	}

	function buildUpdatePayload(): LocataireUpdatePayload | null {
		if (!editDraft.nom.trim() || !editDraft.dateDebut) {
			return null;
		}

		return {
			nom: editDraft.nom.trim(),
			email: editDraft.email.trim() || null,
			date_debut: editDraft.dateDebut,
			date_fin: editDraft.dateFin || null
		};
	}

	function resetCreateDraft() {
		createDraft = {
			idBien: scopedBiens[0] ? String(scopedBiens[0].id || '') : '',
			nom: '',
			email: '',
			dateDebut: new Date().toISOString().slice(0, 10),
			dateFin: ''
		};
	}

	function resolveBienLabel(idBien: Locataire['id_bien']) {
		const bien = biens.find((entry) => String(entry.id || '') === String(idBien || ''));
		if (!bien) {
			return 'Bien non identifié';
		}

		return bien.ville ? `${bien.adresse} - ${bien.ville}` : bien.adresse;
	}

	async function loadLocataires() {
		loading = true;
		errorMessage = '';
		try {
			const [nextBiens, nextLocataires, nextScis] = await Promise.all([
				fetchBiens(),
				fetchLocataires(),
				fetchScis()
			]);
			biens = Array.isArray(nextBiens) ? nextBiens : [];
			locataires = Array.isArray(nextLocataires) ? nextLocataires : [];
			scis = Array.isArray(nextScis) ? nextScis : [];
			const storedActiveSciId = getStoredActiveSciId();
			activeSciId =
				(storedActiveSciId &&
					nextScis.some((sci) => String(sci.id) === storedActiveSciId) &&
					storedActiveSciId) ||
				String(nextScis[0]?.id || '');
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de charger les locataires.');
		} finally {
			loading = false;
		}
	}

	async function handleCreateLocataire() {
		const payload = buildCreatePayload();
		if (!payload) {
			errorMessage = 'Complète le bien, le nom et la date de début avant d’ajouter le locataire.';
			return;
		}

		submitting = true;
		errorMessage = '';

		try {
			const created = await createLocataire(payload);
			locataires = [created, ...locataires];
			resetCreateDraft();
			createDialogOpen = false;
		} catch (error) {
			errorMessage = formatApiErrorMessage(
				error,
				'Impossible d’ajouter le locataire. Vérifie les dates et le bien sélectionné.'
			);
		} finally {
			submitting = false;
		}
	}

	function openEditLocataire(locataire: Locataire) {
		editingLocataire = locataire;
		editDraft = {
			idBien: String(locataire.id_bien || ''),
			nom: locataire.nom || '',
			email: locataire.email || '',
			dateDebut: locataire.date_debut || '',
			dateFin: locataire.date_fin || ''
		};
		editDialogOpen = true;
		errorMessage = '';
	}

	function closeEditLocataire() {
		editDialogOpen = false;
	}

	async function handleUpdateLocataire() {
		if (!editingLocataire?.id) {
			return;
		}

		const payload = buildUpdatePayload();
		if (!payload) {
			errorMessage =
				'Complète le nom et la date de début avant d’enregistrer les modifications.';
			return;
		}

		submitting = true;
		errorMessage = '';

		try {
			const updated = await updateLocataire(editingLocataire.id, payload);
			locataires = locataires.map((locataire) =>
				String(locataire.id || '') === String(updated.id || '') ? updated : locataire
			);
			closeEditLocataire();
		} catch (error) {
			errorMessage = formatApiErrorMessage(
				error,
				'Impossible de modifier le locataire sélectionné.'
			);
		} finally {
			submitting = false;
		}
	}

	function openDeleteLocataire(locataire: Locataire) {
		locatairePendingDelete = locataire;
		deleteDialogOpen = true;
		errorMessage = '';
	}

	function closeDeleteLocataire() {
		deleteDialogOpen = false;
	}

	async function handleDeleteLocataire() {
		if (!locatairePendingDelete?.id) {
			return;
		}

		deleting = true;
		errorMessage = '';

		try {
			await deleteLocataire(locatairePendingDelete.id);
			locataires = locataires.filter(
				(locataire) => String(locataire.id || '') !== String(locatairePendingDelete?.id || '')
			);
			closeDeleteLocataire();
		} catch (error) {
			errorMessage = formatApiErrorMessage(
				error,
				'Impossible de supprimer le locataire sélectionné.'
			);
		} finally {
			deleting = false;
		}
	}
</script>

<svelte:head>
	<title>Locataires — GererSCI</title>
	<meta name="description" content="Référentiel des locataires et suivi d'occupation." />
</svelte:head>

<section class="sci-page-shell">
	<WorkspaceHeader
		eyebrow="Exploitation • occupation"
		title="Referentiel des locataires"
		subtitle="La page sert d’abord a lire l’occupation et la qualite du referentiel. La creation et l’edition s’ouvrent a la demande dans un panneau lateral."
		contextLabel="SCI active"
		contextValue={activeSci?.nom || 'Aucune SCI selectionnee'}
		contextDetail={activeSci
			? `${scopedLocataires.length} locataire(s) • ${activeLocatairesCount} occupation(s) active(s)`
			: 'Choisis une SCI active pour documenter l’occupation bien par bien.'}
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
			label="Locataires suivis"
			value={scopedLocataires.length}
			caption="référentiel de la SCI active"
			trend="up"
			trendValue={scopedLocataires.length > 0 ? 'documenté' : 'à démarrer'}
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Occupations actives"
			value={activeLocatairesCount}
			caption="baux en cours ou ouverts"
			trend="neutral"
			trendValue="suivi"
			tone="success"
			{loading}
		/>
		<KpiCard
			label="Emails documentés"
			value={documentedEmailsCount}
			caption="contacts exploitables"
			trend="neutral"
			trendValue={documentedEmailsCount > 0 ? 'qualifié' : 'à compléter'}
			tone="default"
			{loading}
		/>
	</div>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	{#if loading}
		<OperatorWorkspaceSkeleton
			eyebrow="Chargement occupants"
			title="Préparation du module Locataires"
			description="On aligne la SCI active, les biens rattachés et les périodes d’occupation."
			showRail={true}
		/>
	{:else}
		<WorkspaceActionBar
			eyebrow="Cadre occupation"
			title="Referentiel d’occupation avant loyers"
			description="On documente d’abord le bien, l’occupant et la periode d’occupation. Les loyers viennent ensuite utiliser ce referentiel propre."
		>
			<div class="sci-action-grid">
				<div class="sci-action-card">
					<p class="sci-action-card-title">SCI active</p>
					<p class="sci-action-card-value">{activeSci?.nom || 'Aucune SCI selectionnee'}</p>
					<p class="sci-action-card-body">Le referentiel locataire est filtre par les biens de cette SCI.</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Caracteristiques</p>
					<p class="sci-action-card-value">Bien, nom, email, dates d’occupation</p>
					<p class="sci-action-card-body">On documente un occupant exploitable, pas une simple valeur libre dans un loyer.</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Etape suivante</p>
					<p class="sci-action-card-value">{scopedLocataires.length > 0 ? 'Passer aux loyers' : 'Creer le premier locataire'}</p>
					<p class="sci-action-card-body">Le referentiel sert ensuite le recouvrement, les quittances et la lecture du bien.</p>
				</div>
			</div>
			<div class="mt-5 sci-primary-actions">
				<Button disabled={!activeSci || scopedBiens.length === 0} onclick={() => (createDialogOpen = true)}>
					Ajouter un locataire
				</Button>
				<a href="/loyers"><Button variant="outline">Ouvrir Loyers</Button></a>
				<a href="/biens"><Button variant="outline">Ouvrir Biens</Button></a>
			</div>
			{#snippet aside()}
				<WorkspaceRailCard
					title="Vision"
					description="L’occupation sert de pivot entre le patrimoine et le journal de loyers."
				>
					<div class="space-y-3">
						<div class="sci-action-card">
							<p class="sci-action-card-title">Maintenant</p>
							<p class="sci-action-card-value">
								{!activeSci
									? 'Choisir une SCI active'
									: scopedBiens.length === 0
										? 'Ajouter le premier bien'
										: 'Documenter le premier occupant'}
							</p>
							<p class="sci-action-card-body">Sans bien, puis sans occupant, la chaine locative reste incomplète.</p>
						</div>
						<Button href="/finance" variant="outline" class="w-full justify-start">Voir la finance</Button>
					</div>
				</WorkspaceRailCard>
			{/snippet}
		</WorkspaceActionBar>

		{#if !activeSci}
			<EmptyState
	align="left"
	eyebrow="Pre-requis metier"
	title="Selectionne d’abord une SCI active"
	description="Un locataire doit etre rattache a un bien d’une SCI active. Passe par le portefeuille SCI pour choisir ou creer la societe cible."
	actions={[{ label: 'Ouvrir le portefeuille SCI', href: '/scis' }, { label: 'Retour au cockpit', href: '/dashboard', variant: 'outline' }]}
/>
		{:else if scopedBiens.length === 0}
			<EmptyState
	align="left"
	eyebrow="Pre-requis patrimoine"
	title="Ajoute d’abord un bien a la SCI active"
	description="Le referentiel locataire se construit bien par bien. Sans actif rattache, on ne peut pas documenter l’occupation."
	actions={[{ label: 'Ajouter un bien', href: '/biens' }, { label: 'Verifier la SCI active', href: '/scis', variant: 'outline' }]}
/>
		{/if}

		<Card class="sci-section-card">
			<CardHeader>
				<div class="flex items-end justify-between gap-4">
					<div>
						<CardTitle class="text-lg">Journal des locataires</CardTitle>
						<CardDescription>
							Identité, bien rattaché et période d’occupation de la SCI active.
						</CardDescription>
					</div>
					<p class="text-[0.72rem] font-semibold tracking-[0.22em] uppercase text-muted-foreground">
						{scopedLocataires.length} enregistrements
					</p>
				</div>
			</CardHeader>
			<CardContent class="pt-0">
				{#if scopedLocataires.length === 0}
					<div class="rounded-2xl border border-dashed border-border bg-muted p-8 text-center">
						<p class="text-sm font-medium text-foreground">
							Aucun locataire enregistré pour le moment.
						</p>
						<p class="mt-1 text-sm text-muted-foreground">
							Ajoute une première fiche pour sécuriser la suite du parcours loyers et quittances.
						</p>
					</div>
				{:else}
					<div class="overflow-x-auto rounded-2xl border border-border">
						<table class="min-w-full divide-y divide-border text-sm">
							<thead class="bg-muted">
								<tr>
									<th class="px-4 py-3 text-left font-semibold text-muted-foreground">Locataire</th>
									<th class="px-4 py-3 text-left font-semibold text-muted-foreground">Bien</th>
									<th class="px-4 py-3 text-left font-semibold text-muted-foreground">Occupation</th>
									<th class="px-4 py-3 text-left font-semibold text-muted-foreground">Contact</th>
									<th class="px-4 py-3 text-right font-semibold text-muted-foreground">Actions</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-border">
								{#each scopedLocataires as locataire (String(locataire.id || `${locataire.id_bien}-${locataire.nom}`))}
									<tr class="bg-card">
										<td class="px-4 py-4">
											<p class="font-semibold text-foreground">{locataire.nom}</p>
										</td>
										<td class="px-4 py-4 text-muted-foreground">
											{resolveBienLabel(locataire.id_bien)}
										</td>
										<td class="px-4 py-4 text-muted-foreground">
											{formatFrDate(locataire.date_debut)}
											{#if locataire.date_fin}
												&nbsp;→&nbsp;{formatFrDate(locataire.date_fin)}
											{:else}
												&nbsp;→&nbsp;en cours
											{/if}
										</td>
										<td class="px-4 py-4 text-muted-foreground">
											{locataire.email || 'Email non renseigné'}
										</td>
										<td class="px-4 py-4">
											<div class="flex justify-end gap-2">
												<Button
													size="sm"
													variant="outline"
													disabled={submitting || deleting}
													onclick={() => openEditLocataire(locataire)}
												>
													Modifier
												</Button>
												<Button
													size="sm"
													variant="destructive"
													disabled={busyLocataireId === String(locataire.id || '')}
													onclick={() => openDeleteLocataire(locataire)}
												>
													Supprimer
												</Button>
											</div>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</CardContent>
		</Card>
	{/if}

	<EntityDrawer
		bind:open={createDialogOpen}
		title="Ajouter un locataire"
		description="Cree une fiche locataire complete sans quitter le referentiel d’occupation de la SCI active."
		size="lg"
	>
			{#if !activeSci}
				<p class="sci-inline-alert sci-inline-alert-error">
					Sélectionne d’abord une SCI active avant de créer un locataire.
				</p>
			{:else if scopedBiens.length === 0}
				<p class="sci-inline-alert sci-inline-alert-error">
					Ajoute d’abord un bien à la SCI active avant de créer un locataire.
				</p>
			{:else}
				<div class="grid gap-4 py-2 md:grid-cols-2">
					<label class="sci-field md:col-span-2">
						<span class="sci-field-label">Bien</span>
						<select bind:value={createDraft.idBien} class="sci-select">
							{#each scopedBiens as bien (bien.id)}
								<option value={String(bien.id || '')}>
									{bien.adresse}
									{bien.ville ? ` - ${bien.ville}` : ''}
								</option>
							{/each}
						</select>
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Nom</span>
						<Input bind:value={createDraft.nom} placeholder="Jean Martin" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Email</span>
						<Input bind:value={createDraft.email} placeholder="jean.martin@email.fr" type="email" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Date d'entrée</span>
						<Input bind:value={createDraft.dateDebut} type="date" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Date de sortie</span>
						<Input bind:value={createDraft.dateFin} type="date" />
					</label>
				</div>
			{/if}
		{#snippet footer()}
			<div class="flex justify-end gap-3">
				<Button type="button" variant="outline" onclick={() => (createDialogOpen = false)}>
					Annuler
				</Button>
				<Button type="button" disabled={submitting || !activeSci || scopedBiens.length === 0} onclick={handleCreateLocataire}>
					{submitting ? 'Enregistrement...' : 'Ajouter le locataire'}
				</Button>
			</div>
		{/snippet}
	</EntityDrawer>

	<EntityDrawer
		bind:open={editDialogOpen}
		title="Modifier le locataire"
		description="Ajuste l’identite ou la periode d’occupation du locataire selectionne."
		size="lg"
	>
			{#if editingLocataire}
				<div class="grid gap-4 md:grid-cols-2">
					<div class="sci-field md:col-span-2">
						<span class="sci-field-label">Bien concerné</span>
						<div
							class="rounded-xl border border-border bg-muted px-3 py-2 text-sm font-medium text-foreground"
						>
							{resolveBienLabel(editDraft.idBien)}
						</div>
					</div>
					<label class="sci-field">
						<span class="sci-field-label">Nom</span>
						<Input bind:value={editDraft.nom} />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Email</span>
						<Input bind:value={editDraft.email} type="email" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Date d'entrée</span>
						<Input bind:value={editDraft.dateDebut} type="date" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Date de sortie</span>
						<Input bind:value={editDraft.dateFin} type="date" />
					</label>
				</div>
			{/if}
		{#snippet footer()}
			<div class="flex justify-end gap-3">
				<Button type="button" variant="outline" onclick={closeEditLocataire}>Annuler</Button>
				<Button type="button" disabled={submitting} onclick={handleUpdateLocataire}>
					{submitting ? 'Enregistrement...' : 'Enregistrer les modifications'}
				</Button>
			</div>
		{/snippet}
	</EntityDrawer>

	<Dialog.Dialog bind:open={deleteDialogOpen}>
		<Dialog.DialogContent class="sm:max-w-md">
			<Dialog.DialogHeader>
				<Dialog.DialogTitle>Supprimer le locataire</Dialog.DialogTitle>
				<Dialog.DialogDescription>
					Cette action retire la fiche locataire du référentiel de la SCI active.
				</Dialog.DialogDescription>
			</Dialog.DialogHeader>
			<p class="text-sm leading-relaxed text-muted-foreground">
				{#if locatairePendingDelete}
					Confirme la suppression de <strong>{locatairePendingDelete.nom}</strong>.
				{:else}
					Confirme la suppression du locataire sélectionné.
				{/if}
			</p>
			<Dialog.DialogFooter>
				<Button type="button" variant="outline" onclick={closeDeleteLocataire}>Annuler</Button>
				<Button type="button" variant="destructive" disabled={deleting} onclick={handleDeleteLocataire}>
					{deleting ? 'Suppression...' : 'Confirmer la suppression'}
				</Button>
			</Dialog.DialogFooter>
		</Dialog.DialogContent>
	</Dialog.Dialog>
</section>
