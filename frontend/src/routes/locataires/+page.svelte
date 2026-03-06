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

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">GererSCI • Occupants</p>
		<h1 class="sci-page-title">Référentiel des locataires</h1>
		<p class="sci-page-subtitle">
			Documente les occupants par bien avec identité, email et période d’occupation avant de saisir
			les flux locatifs.
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
		<Card class="sci-section-card">
			<CardHeader>
				<CardTitle class="text-lg">Parcours opérateur</CardTitle>
				<CardDescription>
					Une chaîne propre commence ici: sélectionner un bien, documenter l’occupant, dater
					l’entrée, puis seulement ouvrir la saisie des loyers et des quittances.
				</CardDescription>
			</CardHeader>
			<CardContent class="grid gap-3 pt-0 md:grid-cols-3">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">
						SCI active
					</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{activeSci?.nom || 'Aucune SCI sélectionnée'}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Le référentiel des locataires est filtré sur cette SCI via les biens rattachés.
					</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">
						Caractéristiques obligatoires
					</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						Bien, nom, email, date d’entrée, date de sortie
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						On documente un occupant exploitable, pas une simple chaîne libre dans un loyer.
					</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">
						Étape suivante
					</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{scopedLocataires.length > 0 ? 'Passer aux loyers' : 'Créer le premier locataire'}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Une fois l’occupant créé, le module Loyers peut utiliser un référentiel propre.
					</p>
					<div class="mt-4">
						<a href="/loyers"><Button size="sm" variant="outline">Ouvrir Loyers</Button></a>
					</div>
				</div>
			</CardContent>
		</Card>

		{#if !activeSci}
			<div class="rounded-[1.75rem] border border-slate-200 bg-white/92 p-6 shadow-[0_20px_65px_-45px_rgba(15,23,42,0.5)] dark:border-slate-800 dark:bg-slate-900/84">
				<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">
					Pré-requis métier
				</p>
				<h2 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">
					Sélectionne d’abord une SCI active
				</h2>
				<p class="mt-2 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
					Un locataire doit être rattaché à un bien d’une SCI active. Passe par le portefeuille SCI
					pour choisir ou créer la société cible.
				</p>
				<div class="mt-5 flex flex-wrap gap-3">
					<a href="/scis"><Button>Ouvrir le portefeuille SCI</Button></a>
					<a href="/dashboard"><Button variant="outline">Retour au cockpit</Button></a>
				</div>
			</div>
		{:else if scopedBiens.length === 0}
			<div class="rounded-[1.75rem] border border-slate-200 bg-white/92 p-6 shadow-[0_20px_65px_-45px_rgba(15,23,42,0.5)] dark:border-slate-800 dark:bg-slate-900/84">
				<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">
					Pré-requis patrimoine
				</p>
				<h2 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">
					Ajoute d’abord un bien à la SCI active
				</h2>
				<p class="mt-2 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
					Le référentiel locataire se construit bien par bien. Sans actif rattaché, on ne peut pas
					documenter l’occupation.
				</p>
				<div class="mt-5 flex flex-wrap gap-3">
					<a href="/biens"><Button>Ajouter un bien</Button></a>
					<a href="/scis"><Button variant="outline">Vérifier la SCI active</Button></a>
				</div>
			</div>
		{:else}
			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="text-lg">Nouveau locataire</CardTitle>
					<CardDescription>
						Crée une fiche locataire complète avant de saisir les flux mensuels.
					</CardDescription>
				</CardHeader>
				<CardContent class="grid gap-3 pt-0 md:grid-cols-5">
					<label class="sci-field">
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
					<div class="flex justify-end md:col-span-5">
						<Button disabled={submitting} onclick={handleCreateLocataire}>
							{submitting ? 'Enregistrement...' : 'Ajouter le locataire'}
						</Button>
					</div>
				</CardContent>
			</Card>
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
					<p class="text-[0.72rem] font-semibold tracking-[0.22em] uppercase text-slate-500">
						{scopedLocataires.length} enregistrements
					</p>
				</div>
			</CardHeader>
			<CardContent class="pt-0">
				{#if scopedLocataires.length === 0}
					<div class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center dark:border-slate-700 dark:bg-slate-900">
						<p class="text-sm font-medium text-slate-700 dark:text-slate-200">
							Aucun locataire enregistré pour le moment.
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							Ajoute une première fiche pour sécuriser la suite du parcours loyers et quittances.
						</p>
					</div>
				{:else}
					<div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
						<table class="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
							<thead class="bg-slate-50 dark:bg-slate-900">
								<tr>
									<th class="px-4 py-3 text-left font-semibold text-slate-500">Locataire</th>
									<th class="px-4 py-3 text-left font-semibold text-slate-500">Bien</th>
									<th class="px-4 py-3 text-left font-semibold text-slate-500">Occupation</th>
									<th class="px-4 py-3 text-left font-semibold text-slate-500">Contact</th>
									<th class="px-4 py-3 text-right font-semibold text-slate-500">Actions</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-slate-200 dark:divide-slate-800">
								{#each scopedLocataires as locataire (String(locataire.id || `${locataire.id_bien}-${locataire.nom}`))}
									<tr class="bg-white dark:bg-slate-950">
										<td class="px-4 py-4">
											<p class="font-semibold text-slate-900 dark:text-slate-100">{locataire.nom}</p>
										</td>
										<td class="px-4 py-4 text-slate-600 dark:text-slate-300">
											{resolveBienLabel(locataire.id_bien)}
										</td>
										<td class="px-4 py-4 text-slate-600 dark:text-slate-300">
											{formatFrDate(locataire.date_debut)}
											{#if locataire.date_fin}
												&nbsp;→&nbsp;{formatFrDate(locataire.date_fin)}
											{:else}
												&nbsp;→&nbsp;en cours
											{/if}
										</td>
										<td class="px-4 py-4 text-slate-600 dark:text-slate-300">
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

	<Dialog.Dialog bind:open={editDialogOpen}>
		<Dialog.DialogContent class="sm:max-w-3xl">
			<Dialog.DialogHeader>
				<Dialog.DialogTitle>Modifier le locataire</Dialog.DialogTitle>
				<Dialog.DialogDescription>
					Ajuste l’identité ou la période d’occupation du locataire sélectionné.
				</Dialog.DialogDescription>
			</Dialog.DialogHeader>
			{#if editingLocataire}
				<div class="grid gap-4 md:grid-cols-2">
					<div class="sci-field md:col-span-2">
						<span class="sci-field-label">Bien concerné</span>
						<div
							class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
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
				<Dialog.DialogFooter>
					<Button type="button" variant="outline" onclick={closeEditLocataire}>Annuler</Button>
					<Button type="button" disabled={submitting} onclick={handleUpdateLocataire}>
						{submitting ? 'Enregistrement...' : 'Enregistrer les modifications'}
					</Button>
				</Dialog.DialogFooter>
			{/if}
		</Dialog.DialogContent>
	</Dialog.Dialog>

	<Dialog.Dialog bind:open={deleteDialogOpen}>
		<Dialog.DialogContent class="sm:max-w-md">
			<Dialog.DialogHeader>
				<Dialog.DialogTitle>Supprimer le locataire</Dialog.DialogTitle>
				<Dialog.DialogDescription>
					Cette action retire la fiche locataire du référentiel de la SCI active.
				</Dialog.DialogDescription>
			</Dialog.DialogHeader>
			<p class="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
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
