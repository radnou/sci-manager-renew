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
	import EmptyStateOperator from '$lib/components/EmptyStateOperator.svelte';
	import EntityDrawer from '$lib/components/EntityDrawer.svelte';
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
	<WorkspaceHeader
		eyebrow="Gouvernance • associés et capital"
		title="Associés et gouvernance"
		subtitle="Le registre de gouvernance documente le capital, les rôles et les accès compte réels sans mélanger le sujet au reste de l’exploitation."
		contextLabel="SCI active"
		contextValue={activeSci?.nom || 'Aucune SCI sélectionnée'}
		contextDetail={activeSci
			? `${scopedAssocies.length} associé(s) documenté(s) • ${formatPercent(metrics.totalParts, '0 %')} répartis`
			: 'Choisis une SCI dans le portefeuille avant de travailler la gouvernance.'}
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
		<Button disabled={createDisabled} onclick={() => (createDialogOpen = true)}>Ajouter un associé</Button>
		<Button href="/charges" variant="outline">Charges</Button>
		<Button href="/fiscalite" variant="outline">Fiscalité</Button>
	</WorkspaceHeader>

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
		<EmptyStateOperator
			eyebrow="Pré-requis métier"
			title="Sélectionne d'abord une SCI"
			description="La gouvernance se pilote toujours dans le contexte d'une société précise. Choisis ou crée la SCI cible avant de documenter les associés."
			primaryHref="/scis"
			primaryLabel="Ouvrir le portefeuille SCI"
			secondaryHref="/dashboard"
			secondaryLabel="Retour au cockpit"
		/>
	{:else}
		<WorkspaceActionBar
			eyebrow="Cadre de gouvernance"
			title="Lecture du capital avant intervention"
			description="On contrôle d'abord la répartition du capital, puis les rôles et enfin les accès compte. La gouvernance reste séparée des journaux d'exploitation."
		>
			<div class="sci-action-grid">
				<div class="sci-action-card">
					<p class="sci-action-card-title">SCI active</p>
					<p class="sci-action-card-value">{activeSci.nom}</p>
					<p class="sci-action-card-body">La gouvernance affichée et modifiée est filtrée sur cette SCI.</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Caractéristiques</p>
					<p class="sci-action-card-value">Nom, email, part détenue, rôle, accès connecté</p>
					<p class="sci-action-card-body">Les accès compte restent visibles, sans réduire la gouvernance à un email.</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Étape suivante</p>
					<p class="sci-action-card-value">
						{metrics.total > 0 ? 'Passer au contrôle financier' : 'Structurer la gouvernance'}
					</p>
					<p class="sci-action-card-body">
						Une fois les personnes et les parts documentées, passe aux charges ou à la fiscalité.
					</p>
				</div>
			</div>
			<div class="mt-5 sci-primary-actions">
				<Button disabled={createDisabled} onclick={() => (createDialogOpen = true)}>
					Ajouter un associé
				</Button>
				<Button href="/charges" variant="outline">Ouvrir Charges</Button>
				<Button href="/fiscalite" variant="outline">Ouvrir Fiscalité</Button>
			</div>
			{#snippet aside()}
				<WorkspaceRailCard
					title="Vision"
					description="Un registre propre permet ensuite d'arbitrer charges, fiscalité et répartition des rôles sans angle mort."
				>
					<div class="space-y-3">
						<div class="sci-action-card">
							<p class="sci-action-card-title">Capital restant</p>
							<p class="sci-action-card-value">{formatPercent(metrics.remainingParts, '0 %')}</p>
							<p class="sci-action-card-body">À répartir avant d'atteindre une lecture de gouvernance complète.</p>
						</div>
						<Button href="/dashboard" variant="outline" class="w-full justify-start">
							Retour au cockpit
						</Button>
					</div>
				</WorkspaceRailCard>
			{/snippet}
		</WorkspaceActionBar>

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

	<EntityDrawer
		bind:open={createDialogOpen}
		title="Ajouter un associé"
		description="Crée une ligne de gouvernance pour la SCI active sans quitter le registre du capital."
		size="lg"
	>
		{#snippet children()}
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
			{/if}
		{/snippet}
		{#snippet footer()}
			{#if activeSci}
				<div class="flex flex-wrap justify-end gap-3">
					<Button variant="outline" onclick={() => (createDialogOpen = false)}>Annuler</Button>
					<Button disabled={submitting || createDisabled} onclick={handleCreateAssocie}>
						{submitting ? "Création..." : "Ajouter l'associé"}
					</Button>
				</div>
			{/if}
		{/snippet}
	</EntityDrawer>

	<EntityDrawer
		bind:open={editDialogOpen}
		title="Modifier l’associé"
		description="Mets à jour le rôle, la part ou les coordonnées sans toucher au contexte SCI."
		size="lg"
	>
		{#snippet children()}
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
		{/snippet}
		{#snippet footer()}
			<div class="flex flex-wrap justify-end gap-3">
				<Button variant="outline" onclick={closeEditAssocie}>Annuler</Button>
				<Button disabled={submitting} onclick={handleUpdateAssocie}>
					{submitting ? 'Enregistrement...' : 'Enregistrer les modifications'}
				</Button>
			</div>
		{/snippet}
	</EntityDrawer>

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
