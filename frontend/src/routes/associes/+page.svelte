<script lang="ts">
	import { onMount } from 'svelte';
	import {
		createAssocie,
		deleteAssocie,
		fetchAssocies,
		fetchScis,
		updateAssocie,
		type Associe,
		type AssocieCreatePayload,
		type AssocieUpdatePayload,
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
	import { ASSOCIE_ROLE_OPTIONS, calculateAssociateMetrics } from '$lib/high-value/associes';
	import { formatPercent } from '$lib/high-value/formatters';
	import { formatApiErrorMessage, mapAssociateRoleLabel } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let associes = $state<Associe[]>([]);
	let scis = $state<SCIOverview[]>([]);
	let activeSciId = $state('');
	let loading = $state(true);
	let submitting = $state(false);
	let deleting = $state(false);
	let errorMessage = $state('');
	let createDialogOpen = $state(false);
	let editDialogOpen = $state(false);
	let deleteDialogOpen = $state(false);
	let editingAssocie = $state<Associe | null>(null);
	let associePendingDelete = $state<Associe | null>(null);

	let createDraft = $state({
		nom: '',
		email: '',
		part: '',
		role: 'associe'
	});

	let editDraft = $state({
		nom: '',
		email: '',
		part: '',
		role: 'associe'
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
	let scopedAssocies = $derived(
		activeSci
			? associes.filter((associe) => String(associe.id_sci || '') === String(activeSci.id))
			: associes
	);
	let metrics = $derived(calculateAssociateMetrics(scopedAssocies));
	let createDisabled = $derived(!activeSci || metrics.remainingParts <= 0);
	let busyAssocieId = $derived(
		deleting
			? String(associePendingDelete?.id || '')
			: submitting && editingAssocie
				? String(editingAssocie.id || '')
				: ''
	);
	$effect(() => {
		if (!editDialogOpen) {
			editingAssocie = null;
		}
	});
	$effect(() => {
		if (!deleteDialogOpen) {
			associePendingDelete = null;
		}
	});

	onMount(loadAssocies);

	async function loadAssocies() {
		loading = true;
		errorMessage = '';
		try {
			const [nextScis, nextAssocies] = await Promise.all([fetchScis(), fetchAssocies()]);
			scis = Array.isArray(nextScis) ? nextScis : [];
			associes = Array.isArray(nextAssocies) ? nextAssocies : [];
			const storedActiveSciId = getStoredActiveSciId();
			activeSciId =
				(storedActiveSciId &&
					nextScis.some((sci) => String(sci.id) === storedActiveSciId) &&
					storedActiveSciId) ||
				String(nextScis[0]?.id || '');
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, "Impossible de charger la gouvernance de la SCI.");
		} finally {
			loading = false;
		}
	}

	function buildCreatePayload(): AssocieCreatePayload | null {
		if (!activeSci?.id || !createDraft.nom.trim() || !createDraft.part) {
			return null;
		}

		return {
			id_sci: activeSci.id,
			nom: createDraft.nom.trim(),
			email: createDraft.email.trim() || null,
			part: Number(createDraft.part),
			role: createDraft.role,
			user_id: null
		};
	}

	function buildUpdatePayload(): AssocieUpdatePayload | null {
		if (!editDraft.nom.trim() || !editDraft.part) {
			return null;
		}

		return {
			nom: editDraft.nom.trim(),
			email: editDraft.email.trim() || null,
			part: Number(editDraft.part),
			role: editDraft.role
		};
	}

	function resetCreateDraft() {
		createDraft = {
			nom: '',
			email: '',
			part: '',
			role: 'associe'
		};
	}

	async function handleCreateAssocie() {
		const payload = buildCreatePayload();
		if (!payload) {
			errorMessage = "Complète le nom, la part et la SCI active avant d'ajouter un associé.";
			return;
		}

		submitting = true;
		errorMessage = '';
		try {
			const created = await createAssocie(payload);
			associes = [...associes, created];
			resetCreateDraft();
			createDialogOpen = false;
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, "Impossible d'ajouter l'associé sélectionné.");
		} finally {
			submitting = false;
		}
	}

	function openEditAssocie(associe: Associe) {
		editingAssocie = associe;
		editDraft = {
			nom: associe.nom || '',
			email: associe.email || '',
			part: associe.part != null ? String(associe.part) : '',
			role: associe.role || 'associe'
		};
		editDialogOpen = true;
		errorMessage = '';
	}

	function closeEditAssocie() {
		editDialogOpen = false;
	}

	async function handleUpdateAssocie() {
		if (!editingAssocie?.id) {
			return;
		}

		const payload = buildUpdatePayload();
		if (!payload) {
			errorMessage = "Complète le nom et la part avant d'enregistrer les modifications.";
			return;
		}

		submitting = true;
		errorMessage = '';
		try {
			const updated = await updateAssocie(editingAssocie.id, payload);
			associes = associes.map((associe) =>
				String(associe.id || '') === String(updated.id || '') ? updated : associe
			);
			closeEditAssocie();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, "Impossible de modifier l'associé sélectionné.");
		} finally {
			submitting = false;
		}
	}

	function openDeleteAssocie(associe: Associe) {
		associePendingDelete = associe;
		deleteDialogOpen = true;
		errorMessage = '';
	}

	function closeDeleteAssocie() {
		deleteDialogOpen = false;
	}

	async function handleDeleteAssocie() {
		if (!associePendingDelete?.id) {
			return;
		}

		deleting = true;
		errorMessage = '';
		try {
			await deleteAssocie(associePendingDelete.id);
			associes = associes.filter(
				(associe) => String(associe.id || '') !== String(associePendingDelete?.id || '')
			);
			closeDeleteAssocie();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, "Impossible de supprimer l'associé sélectionné.");
		} finally {
			deleting = false;
		}
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">GererSCI • Gouvernance</p>
		<h1 class="sci-page-title">Associés et gouvernance</h1>
		<p class="sci-page-subtitle">
			Documente la gouvernance de la SCI active avec une répartition claire du capital, les rôles et
			les accès compte réellement portés par les membres connectés.
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
			label="Associés suivis"
			value={metrics.total}
			caption="gouvernance documentée"
			trend={metrics.total > 0 ? 'up' : 'neutral'}
			trendValue={metrics.total > 0 ? 'à jour' : 'à structurer'}
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Capital réparti"
			value={formatPercent(metrics.totalParts, '0 %')}
			caption={`${formatPercent(metrics.remainingParts, '0 %')} restant à répartir`}
			trend={metrics.remainingParts > 0 ? 'neutral' : 'up'}
			trendValue={metrics.remainingParts > 0 ? 'à compléter' : 'cohérent'}
			tone={metrics.remainingParts > 0 ? 'warning' : 'success'}
			{loading}
		/>
		<KpiCard
			label="Accès compte"
			value={metrics.accountMembers}
			caption="membre(s) liés à une session"
			trend={metrics.accountMembers > 0 ? 'up' : 'neutral'}
			trendValue={metrics.accountMembers > 1 ? 'partagé' : 'centralisé'}
			tone="default"
			{loading}
		/>
	</div>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	{#if loading}
		<OperatorWorkspaceSkeleton
			eyebrow="Chargement gouvernance"
			title="Préparation du registre des associés"
			description="On aligne la SCI active, la répartition du capital et les accès compte."
		/>
	{:else if !activeSci}
		<div class="rounded-[1.75rem] border border-slate-200 bg-white/92 p-6 shadow-[0_20px_65px_-45px_rgba(15,23,42,0.5)] dark:border-slate-800 dark:bg-slate-900/84">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Pré-requis métier</p>
			<h2 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">Sélectionne d’abord une SCI</h2>
			<p class="mt-2 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
				La gouvernance se pilote toujours dans le contexte d’une société précise. Choisis ou crée la
				SCI cible avant de documenter les associés.
			</p>
			<div class="mt-5 flex flex-wrap gap-3">
				<a href="/scis"><Button>Ouvrir le portefeuille SCI</Button></a>
				<a href="/dashboard"><Button variant="outline">Retour au cockpit</Button></a>
			</div>
		</div>
	{:else}
		<Card class="sci-section-card">
			<CardHeader>
				<div class="flex flex-wrap items-center justify-between gap-3">
					<div>
						<CardTitle class="text-lg">Lecture et actions</CardTitle>
						<CardDescription>
							Commence par la répartition du capital, puis qualifie le rôle de chaque personne et garde le
							repérage des accès compte séparé du capital pur.
						</CardDescription>
					</div>
					<Button disabled={createDisabled} onclick={() => (createDialogOpen = true)}>
						Nouvel associé
					</Button>
				</div>
			</CardHeader>
			<CardContent class="grid gap-3 pt-0 md:grid-cols-3">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">SCI active</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{activeSci.nom}</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						La gouvernance affichée et modifiée est filtrée sur cette SCI.
					</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Caractéristiques</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						Nom, email, part détenue, rôle, accès connecté
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Les accès compte restent visibles, mais la gouvernance n’est plus réduite à un email.
					</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Étape suivante</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{metrics.total > 0 ? 'Documenter les charges' : 'Structurer la gouvernance'}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Une fois les personnes et les parts documentées, passe au contrôle des charges ou aux arbitrages
						fiscaux.
					</p>
					<div class="mt-4 flex flex-wrap gap-2">
						<a href="/charges"><Button size="sm" variant="outline">Ouvrir Charges</Button></a>
						<a href="/fiscalite"><Button size="sm" variant="outline">Ouvrir Fiscalité</Button></a>
					</div>
				</div>
			</CardContent>
		</Card>

		<Card class="sci-section-card">
				<CardHeader>
					<div class="flex items-end justify-between gap-4">
						<div>
							<CardTitle class="text-lg">Registre de gouvernance</CardTitle>
							<CardDescription>
								Capital, rôles et statut d’accès compte de la SCI active.
							</CardDescription>
						</div>
						<p class="text-[0.72rem] font-semibold tracking-[0.2em] uppercase text-slate-500">
							{scopedAssocies.length} enregistrement{scopedAssocies.length > 1 ? 's' : ''}
						</p>
					</div>
				</CardHeader>
				<CardContent class="grid gap-3 pt-0">
					{#if scopedAssocies.length === 0}
						<div class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
							Aucun associé documenté pour l’instant. Commence par renseigner la gouvernance de la SCI active.
						</div>
					{:else}
						{#each scopedAssocies as associe (String(associe.id))}
							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<div class="flex flex-wrap items-start justify-between gap-3">
									<div>
										<div class="flex flex-wrap items-center gap-2">
											<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">{associe.nom}</p>
											<span class="rounded-full bg-slate-200 px-2.5 py-1 text-[11px] font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
												{mapAssociateRoleLabel(associe.role)}
											</span>
											{#if associe.is_account_member}
												<span class="rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-semibold text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200">
													Accès compte
												</span>
											{/if}
										</div>
										<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
											{associe.email || 'Email non renseigné'}
										</p>
									</div>
									<div class="text-right">
										<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Part détenue</p>
										<p class="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">
											{formatPercent(associe.part, 'N/A')}
										</p>
									</div>
								</div>
								<div class="mt-4 flex flex-wrap justify-end gap-2">
									<Button
										size="sm"
										variant="outline"
										onclick={() => openEditAssocie(associe)}
										disabled={submitting || deleting}
									>
										Modifier
									</Button>
									<Button
										size="sm"
										variant="outline"
										onclick={() => openDeleteAssocie(associe)}
										disabled={submitting || deleting || associe.is_account_member || busyAssocieId === String(associe.id || '')}
									>
										{associe.is_account_member ? 'Accès protégé' : 'Supprimer'}
									</Button>
								</div>
							</div>
						{/each}
					{/if}
				</CardContent>
		</Card>
	{/if}

	<Dialog.Dialog bind:open={createDialogOpen}>
		<Dialog.Content class="sm:max-w-[36rem]">
			<Dialog.Header>
				<Dialog.Title>Ajouter un associé</Dialog.Title>
				<Dialog.Description>
					Crée une ligne de gouvernance pour la SCI active sans quitter le registre du capital.
				</Dialog.Description>
			</Dialog.Header>
			{#if !activeSci}
				<p class="sci-inline-alert sci-inline-alert-error">
					Sélectionne d’abord une SCI active avant d’ajouter un associé.
				</p>
			{:else}
				<div class="grid gap-4 py-2">
					<label class="sci-field">
						<span class="sci-field-label">Nom</span>
						<Input bind:value={createDraft.nom} placeholder="Camille Bernard" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Email</span>
						<Input bind:value={createDraft.email} type="email" placeholder="camille@sci.local" />
					</label>
					<div class="grid gap-4 md:grid-cols-2">
						<label class="sci-field">
							<span class="sci-field-label">Part détenue (%)</span>
							<Input bind:value={createDraft.part} type="number" min="1" max="100" step="0.5" />
						</label>
						<label class="sci-field">
							<span class="sci-field-label">Rôle</span>
							<select bind:value={createDraft.role} class="sci-select">
								{#each ASSOCIE_ROLE_OPTIONS as roleOption (roleOption.value)}
									<option value={roleOption.value}>{roleOption.label}</option>
								{/each}
							</select>
						</label>
					</div>
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
						<p class="font-semibold text-slate-900 dark:text-slate-100">
							Capital restant à répartir: {formatPercent(metrics.remainingParts, '0 %')}
						</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							Les associés créés ici n’ouvrent pas automatiquement un accès compte. Les membres déjà
							connectés restent signalés dans le registre.
						</p>
					</div>
				</div>
				<Dialog.Footer>
					<Button variant="outline" onclick={() => (createDialogOpen = false)}>Annuler</Button>
					<Button disabled={submitting || createDisabled} onclick={handleCreateAssocie}>
						{submitting ? "Création..." : "Ajouter l'associé"}
					</Button>
				</Dialog.Footer>
			{/if}
		</Dialog.Content>
	</Dialog.Dialog>

	<Dialog.Dialog bind:open={editDialogOpen}>
		<Dialog.Content class="sm:max-w-[36rem]">
			<Dialog.Header>
				<Dialog.Title>Modifier l’associé</Dialog.Title>
				<Dialog.Description>
					Mets à jour le rôle, la part ou les coordonnées sans toucher au contexte SCI.
				</Dialog.Description>
			</Dialog.Header>
			<div class="grid gap-4 py-2">
				<label class="sci-field">
					<span class="sci-field-label">Nom</span>
					<Input bind:value={editDraft.nom} />
				</label>
				<label class="sci-field">
					<span class="sci-field-label">Email</span>
					<Input bind:value={editDraft.email} type="email" />
				</label>
				<div class="grid gap-4 md:grid-cols-2">
					<label class="sci-field">
						<span class="sci-field-label">Part détenue (%)</span>
						<Input bind:value={editDraft.part} type="number" min="1" max="100" step="0.5" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Rôle</span>
						<select bind:value={editDraft.role} class="sci-select">
							{#each ASSOCIE_ROLE_OPTIONS as roleOption (roleOption.value)}
								<option value={roleOption.value}>{roleOption.label}</option>
							{/each}
						</select>
					</label>
				</div>
			</div>
			<Dialog.Footer>
				<Button variant="outline" onclick={closeEditAssocie}>Annuler</Button>
				<Button disabled={submitting} onclick={handleUpdateAssocie}>
					{submitting ? 'Enregistrement...' : 'Enregistrer les modifications'}
				</Button>
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Dialog>

	<Dialog.Dialog bind:open={deleteDialogOpen}>
		<Dialog.Content class="sm:max-w-[32rem]">
			<Dialog.Header>
				<Dialog.Title>Supprimer cet associé ?</Dialog.Title>
				<Dialog.Description>
					Cette action retire la ligne de gouvernance de la SCI active. Les accès compte protégés ne sont
					pas supprimables ici.
				</Dialog.Description>
			</Dialog.Header>
			<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
				<p class="font-semibold text-slate-900 dark:text-slate-100">{associePendingDelete?.nom}</p>
				<p class="mt-1 text-slate-500 dark:text-slate-400">
					{mapAssociateRoleLabel(associePendingDelete?.role)} • {formatPercent(associePendingDelete?.part, 'N/A')}
				</p>
			</div>
			<Dialog.Footer>
				<Button variant="outline" onclick={closeDeleteAssocie}>Annuler</Button>
				<Button disabled={deleting} onclick={handleDeleteAssocie}>
					{deleting ? 'Suppression...' : 'Confirmer la suppression'}
				</Button>
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Dialog>
</section>
