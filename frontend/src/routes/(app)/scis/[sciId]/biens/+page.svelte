<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { SCIDetail, Bien, SubscriptionEntitlements } from '$lib/api';
	import { fetchSciBiensList, deleteBien, fetchSubscriptionEntitlements } from '$lib/api';

	type BienListItem = Bien;
	import { formatEur } from '$lib/high-value/formatters';
	import { MapPin, Plus, LayoutGrid, List, Pencil, Trash2, Receipt, Loader2, TrendingUp, Wallet, ArrowUpRight, Upload, CircleCheck, CircleAlert, TriangleAlert } from 'lucide-svelte';
	import BienModal from '$lib/components/fiche-bien/modals/BienModal.svelte';
	import ImportCsvModal from '$lib/components/ImportCsvModal.svelte';
	import { addToast } from '$lib/components/ui/toast';
	import ConfirmDeleteModal from '$lib/components/ConfirmDeleteModal.svelte';
	import RoleGate from '$lib/components/RoleGate.svelte';
	import LockedAction from '$lib/components/LockedAction.svelte';

	const sci = getContext<SCIDetail>('sci');
	const subscription = getContext<SubscriptionEntitlements>('subscription');
	const isDemo = !subscription?.is_active;
	const sciId = getContext<string>('sciId');
	const userRole = getContext<string>('userRole');

	let isGerant = $derived(userRole === 'gerant');
	let showBienModal = $state(false);
	let showImportModal = $state(false);
	let viewMode = $state<'grid' | 'list'>('grid');
	let deletingId = $state<string | null>(null);
	let confirmingDeleteId = $state<string | null>(null);
	let entitlements = $state<SubscriptionEntitlements | null>(null);

	let canCreateBien = $derived(
		!entitlements || entitlements.remaining_biens == null || entitlements.remaining_biens > 0
	);

	function handleNewBienClick() {
		if (canCreateBien) {
			showBienModal = true;
		} else if (entitlements) {
			addToast({
				title: 'Limite atteinte',
				description: `Votre plan ${entitlements.plan_name} est limité à ${entitlements.max_biens} biens. Passez au plan supérieur pour en ajouter davantage.`,
				variant: 'default',
				timeoutMs: 6000
			});
		}
	}

	let biens: BienListItem[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);
	let deleteTargetBien = $derived(
		confirmingDeleteId ? biens.find(b => b.id != null && String(b.id) === confirmingDeleteId) ?? null : null
	);

	onMount(() => {
		fetchSubscriptionEntitlements().then((ent) => { entitlements = ent; }).catch(() => {});
	});

	$effect(() => {
		loadBiens();
	});

	async function loadBiens() {
		loading = true;
		error = null;
		try {
			biens = await fetchSciBiensList(sciId);
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger la liste des biens.';
			biens = [];
		} finally {
			loading = false;
		}
	}

	async function handleDeleteBien(bien: BienListItem) {
		if (!bien.id) return;

		deletingId = String(bien.id);
		try {
			await deleteBien(bien.id);
			addToast({ title: 'Bien supprimé', description: `"${bien.adresse}" a été supprimé.`, variant: 'success' });
			await loadBiens();
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Erreur lors de la suppression.', variant: 'error' });
		} finally {
			deletingId = null;
			confirmingDeleteId = null;
		}
	}

	function formatRendement(value: number | undefined | null): string {
		if (value == null) return '--';
		return `${value.toFixed(1)} %`;
	}

	const statutBadge: Record<string, string> = {
		loue: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
		vacant: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
		travaux: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
	};

	const statutLabel: Record<string, string> = {
		loue: 'Occupé',
		vacant: 'Vacant',
		travaux: 'Travaux'
	};

	function getStatut(bien: BienListItem): string {
		return bien.statut || 'vacant';
	}

	const typeBienLabel: Record<string, string> = {
		appartement: 'Appartement',
		maison: 'Maison',
		immeuble: 'Immeuble',
		local_commercial: 'Local commercial',
		parking: 'Parking / Box',
		autre: 'Autre'
	};

	const typeLocatifLabel: Record<string, string> = {
		nu: 'Location nue',
		meuble: 'Meublé',
		mixte: 'Mixte'
	};

	function getBienTypeLabel(bien: BienListItem): string | null {
		if (bien.type_bien) return typeBienLabel[bien.type_bien] ?? bien.type_bien;
		return null;
	}

	function getLocatifLabel(bien: BienListItem): string | null {
		if (bien.type_locatif) return typeLocatifLabel[bien.type_locatif] ?? bien.type_locatif;
		return null;
	}

	type ObligationStatus = { level: 'green' | 'orange' | 'red'; tooltip: string };

	function getObligationStatus(bien: BienListItem): ObligationStatus {
		const statut = bien.statut || 'vacant';
		const hasBail = statut === 'loue';
		const missing: string[] = [];

		if (!hasBail) {
			missing.push('Pas de bail actif');
		}

		// If the bien is marked as "loue" but lacks data that indicates a locataire,
		// we consider it met. We can only check from the list data.
		// PNO and locataire presence are inferred from statut: if loue, locataire is assumed present.
		// Without extra API data on the list endpoint, we use statut as proxy.

		if (statut === 'vacant') {
			return { level: 'red', tooltip: 'Critique : ' + missing.join(', ') };
		}

		if (statut === 'travaux') {
			return { level: 'orange', tooltip: 'En travaux — bail et locataire en attente' };
		}

		// loue — all met
		return { level: 'green', tooltip: 'Toutes les obligations sont remplies' };
	}

	const obligationDot: Record<string, string> = {
		green: 'bg-emerald-500 dark:bg-emerald-400',
		orange: 'bg-amber-500 dark:bg-amber-400',
		red: 'bg-rose-500 dark:bg-rose-400'
	};

	const obligationIcon: Record<string, typeof CircleCheck> = {
		green: CircleCheck,
		orange: TriangleAlert,
		red: CircleAlert
	};

	const obligationIconColor: Record<string, string> = {
		green: 'text-emerald-500 dark:text-emerald-400',
		orange: 'text-amber-500 dark:text-amber-400',
		red: 'text-rose-500 dark:text-rose-400'
	};
</script>

<svelte:head><title>Biens | {sci.nom} | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<div class="flex items-center justify-between gap-3">
			<h1 class="sci-page-title">Biens</h1>
			<div class="flex items-center gap-2">
				<!-- View toggle -->
				{#if biens.length > 0}
					<div class="inline-flex rounded-lg border border-slate-200 p-0.5 dark:border-slate-700" role="radiogroup" aria-label="Mode d'affichage">
						<button
							onclick={() => viewMode = 'grid'}
							class="rounded-md p-1.5 transition-colors {viewMode === 'grid' ? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}"
							aria-label="Affichage en grille"
							aria-checked={viewMode === 'grid'}
							role="radio"
						>
							<LayoutGrid class="h-4 w-4" />
						</button>
						<button
							onclick={() => viewMode = 'list'}
							class="rounded-md p-1.5 transition-colors {viewMode === 'list' ? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}"
							aria-label="Affichage en liste"
							aria-checked={viewMode === 'list'}
							role="radio"
						>
							<List class="h-4 w-4" />
						</button>
					</div>
				{/if}

				<RoleGate>
					<LockedAction {isDemo} action="importer des biens">
						<button
							onclick={() => showImportModal = true}
							class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
						>
							<Upload class="h-4 w-4" />
							Importer (CSV)
						</button>
					</LockedAction>
					<LockedAction {isDemo} action="ajouter un bien">
						{#if canCreateBien}
							<button
								onclick={() => showBienModal = true}
								class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700"
							>
								<Plus class="h-4 w-4" />
								Ajouter un bien
							</button>
						{:else}
							<button
								onclick={handleNewBienClick}
								class="inline-flex items-center gap-2 rounded-lg border border-sky-300 bg-sky-50 px-4 py-2 text-sm font-medium text-sky-700 opacity-75 transition-colors hover:bg-sky-100 dark:border-sky-700 dark:bg-sky-950/30 dark:text-sky-300 dark:hover:bg-sky-950/50"
							>
								<Plus class="h-4 w-4" />
								Ajouter un bien
								<span class="text-xs">(Limite atteinte)</span>
							</button>
						{/if}
					</LockedAction>
				</RoleGate>
			</div>
		</div>
	</header>
	{#if isGerant && !canCreateBien && entitlements}
		<div class="mt-3 flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-800 dark:bg-amber-950/30">
			<p class="text-sm text-amber-800 dark:text-amber-200">
				Vous avez atteint la limite de votre plan {entitlements.plan_name} ({entitlements.max_biens} biens). Passez au plan supérieur pour ajouter plus de biens.
			</p>
			<a
				href="/pricing"
				target="_blank"
				rel="noopener noreferrer"
				class="ml-4 inline-flex shrink-0 items-center gap-1 rounded-lg bg-amber-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-amber-700"
			>
				Changer de plan
				<ArrowUpRight class="h-3.5 w-3.5" />
			</a>
		</div>
	{/if}

	{#if loading}
		<div class="sci-loading" aria-label="Chargement"></div>
	{:else if error}
		<div class="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30">
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={loadBiens}
				class="mt-3 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				Réessayer
			</button>
		</div>
	{:else if biens.length === 0}
		<div class="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-16 dark:border-slate-700">
			<MapPin class="mb-3 h-10 w-10 text-slate-300 dark:text-slate-600" />
			<p class="text-sm font-medium text-slate-600 dark:text-slate-400">Aucun bien enregistré</p>
			<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
				{#if isGerant}
					Cliquez sur "Ajouter un bien" pour commencer.
				{:else}
					Le gérant n'a pas encore ajouté de bien.
				{/if}
			</p>
		</div>
	{:else if viewMode === 'grid'}
		<!-- Grid View -->
		<div class="sci-stagger mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each biens as bien (bien.id)}
				{@const statut = getStatut(bien)}
				{@const badgeClass = statutBadge[statut] ?? statutBadge['vacant']}
				{@const label = statutLabel[statut] ?? statut}
				{@const isDeleting = deletingId != null && bien.id != null && deletingId === String(bien.id)}
				{@const obligation = getObligationStatus(bien)}
				<div
					class="group rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700"
				>
					<!-- Header: address + badge -->
					<div class="flex items-start justify-between gap-2">
						<div class="flex items-center gap-2">
							<span
								class="relative inline-block h-2.5 w-2.5 shrink-0 rounded-full {obligationDot[obligation.level]}"
								title={obligation.tooltip}
								aria-label={obligation.tooltip}
							></span>
							<a
								href={`/scis/${sciId}/biens/${bien.id}`}
								class="font-semibold text-slate-900 hover:text-sky-600 dark:text-slate-100 dark:hover:text-sky-400"
							>
								{bien.adresse}
							</a>
						</div>
						<span class="inline-flex shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-medium {badgeClass}">
							{label}
						</span>
					</div>

					<!-- Location -->
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						{bien.ville ?? ''} {bien.code_postal ?? ''}
					</p>

					<!-- Type + Rent -->
					<div class="mt-3 flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
						{#if getBienTypeLabel(bien)}
							<span class="rounded-full bg-slate-100 px-2 py-0.5 dark:bg-slate-800">
								{getBienTypeLabel(bien)}
							</span>
						{/if}
						{#if getLocatifLabel(bien)}
							<span class="rounded-full bg-slate-100 px-2 py-0.5 dark:bg-slate-800">
								{getLocatifLabel(bien)}
							</span>
						{/if}
						{#if bien.loyer_cc}
							<span class="font-medium text-slate-700 dark:text-slate-300">
								{formatEur(bien.loyer_cc)}/mois
							</span>
						{/if}
					</div>

					<!-- KPIs: rendement + cashflow -->
					{#if bien.rentabilite_brute != null || bien.cashflow_annuel != null}
						<div class="mt-4 flex flex-col gap-1.5 border-t border-slate-100 pt-3 dark:border-slate-800">
							{#if bien.rentabilite_brute != null}
								<div class="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
									<TrendingUp class="h-3.5 w-3.5 text-sky-500" />
									<span>Rendement brut :</span>
									<span class="font-semibold text-slate-800 dark:text-slate-200">{formatRendement(bien.rentabilite_brute)}</span>
								</div>
							{/if}
							{#if bien.cashflow_annuel != null}
								<div class="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
									<Wallet class="h-3.5 w-3.5 {bien.cashflow_annuel >= 0 ? 'text-emerald-500' : 'text-rose-500'}" />
									<span>Cashflow :</span>
									<span class="font-semibold {bien.cashflow_annuel >= 0 ? 'text-emerald-700 dark:text-emerald-400' : 'text-rose-700 dark:text-rose-400'}">
										{bien.cashflow_annuel >= 0 ? '+' : ''}{formatEur(bien.cashflow_annuel)}/an
									</span>
								</div>
							{/if}
						</div>
					{/if}

					<!-- Actions (gérant only) -->
					<RoleGate>
						<div class="mt-4 flex items-center gap-2 border-t border-slate-100 pt-3 dark:border-slate-800">
							<a
								href={`/scis/${sciId}/biens/${bien.id}`}
								class="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
							>
								<Pencil class="h-3.5 w-3.5" />
								Modifier
							</a>
							<button
								onclick={() => { confirmingDeleteId = bien.id != null ? String(bien.id) : null; }}
								disabled={isDeleting}
								class="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-rose-600 transition-colors hover:bg-rose-50 hover:text-rose-700 disabled:opacity-50 dark:text-rose-400 dark:hover:bg-rose-950/30 dark:hover:text-rose-300"
							>
								{#if isDeleting}
									<Loader2 class="h-3.5 w-3.5 animate-spin" />
								{:else}
									<Trash2 class="h-3.5 w-3.5" />
								{/if}
								Supprimer
							</button>
							<a
								href={`/scis/${sciId}/biens/${bien.id}#loyers`}
								class="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-sky-600 transition-colors hover:bg-sky-50 hover:text-sky-700 dark:text-sky-400 dark:hover:bg-sky-950/30 dark:hover:text-sky-300"
							>
								<Receipt class="h-3.5 w-3.5" />
								Quittance
							</a>
						</div>
					</RoleGate>
				</div>
			{/each}
		</div>
	{:else}
		<!-- List/Table View -->
		<div class="mt-6 overflow-x-auto rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
			<table class="w-full text-left text-sm">
				<thead>
					<tr class="border-b border-slate-100 dark:border-slate-800">
						<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Adresse</th>
						<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Ville</th>
						<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Type</th>
						<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 text-right">Loyer/mois</th>
						<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 text-right">Rendement</th>
						<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 text-right">Cashflow/an</th>
						<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Statut</th>
						<RoleGate>
							<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Actions</th>
						</RoleGate>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100 dark:divide-slate-800">
					{#each biens as bien (bien.id)}
						{@const statut = getStatut(bien)}
						{@const badgeClass = statutBadge[statut] ?? statutBadge['vacant']}
						{@const label = statutLabel[statut] ?? statut}
						{@const isDeleting = deletingId != null && bien.id != null && deletingId === String(bien.id)}
						{@const obligation = getObligationStatus(bien)}
						<tr class="transition-colors hover:bg-slate-50 dark:hover:bg-slate-900/50">
							<td class="px-4 py-3">
								<div class="flex items-center gap-2">
									<span
										class="inline-block h-2 w-2 shrink-0 rounded-full {obligationDot[obligation.level]}"
										title={obligation.tooltip}
										aria-label={obligation.tooltip}
									></span>
									<a
										href={`/scis/${sciId}/biens/${bien.id}`}
										class="font-medium text-slate-900 hover:text-sky-600 dark:text-slate-100 dark:hover:text-sky-400"
									>
										{bien.adresse}
									</a>
								</div>
							</td>
							<td class="whitespace-nowrap px-4 py-3 text-slate-500 dark:text-slate-400">
								{bien.ville ?? '--'} {bien.code_postal ?? ''}
							</td>
							<td class="whitespace-nowrap px-4 py-3">
								{#if getBienTypeLabel(bien)}
									<span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs dark:bg-slate-800 dark:text-slate-300">
										{getBienTypeLabel(bien)}
									</span>
								{:else if getLocatifLabel(bien)}
									<span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs dark:bg-slate-800 dark:text-slate-300">
										{getLocatifLabel(bien)}
									</span>
								{:else}
									<span class="text-slate-400 dark:text-slate-500">--</span>
								{/if}
							</td>
							<td class="whitespace-nowrap px-4 py-3 text-right font-medium text-slate-700 dark:text-slate-300">
								{bien.loyer_cc ? `${formatEur(bien.loyer_cc)}` : '--'}
							</td>
							<td class="whitespace-nowrap px-4 py-3 text-right text-slate-700 dark:text-slate-300">
								{formatRendement(bien.rentabilite_brute)}
							</td>
							<td class="whitespace-nowrap px-4 py-3 text-right">
								{#if bien.cashflow_annuel != null}
									<span class="font-medium {bien.cashflow_annuel >= 0 ? 'text-emerald-700 dark:text-emerald-400' : 'text-rose-700 dark:text-rose-400'}">
										{bien.cashflow_annuel >= 0 ? '+' : ''}{formatEur(bien.cashflow_annuel)}
									</span>
								{:else}
									<span class="text-slate-400 dark:text-slate-500">--</span>
								{/if}
							</td>
							<td class="whitespace-nowrap px-4 py-3">
								<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {badgeClass}">
									{label}
								</span>
							</td>
							<RoleGate>
								<td class="whitespace-nowrap px-4 py-3">
									<div class="flex items-center gap-1">
										<a
											href={`/scis/${sciId}/biens/${bien.id}`}
											class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
											title="Modifier"
											aria-label="Modifier {bien.adresse}"
										>
											<Pencil class="h-4 w-4" />
										</a>
										<button
											onclick={() => { confirmingDeleteId = bien.id != null ? String(bien.id) : null; }}
											disabled={isDeleting}
											class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50 dark:hover:bg-rose-950/30 dark:hover:text-rose-400"
											title="Supprimer"
											aria-label="Supprimer {bien.adresse}"
										>
											{#if isDeleting}
												<Loader2 class="h-4 w-4 animate-spin" />
											{:else}
												<Trash2 class="h-4 w-4" />
											{/if}
										</button>
										<a
											href={`/scis/${sciId}/biens/${bien.id}#loyers`}
											class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-sky-50 hover:text-sky-600 dark:hover:bg-sky-950/30 dark:hover:text-sky-400"
											title="Quittance"
											aria-label="Quittance {bien.adresse}"
										>
											<Receipt class="h-4 w-4" />
										</a>
									</div>
								</td>
							</RoleGate>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		{/if}

	<BienModal bind:open={showBienModal} {sciId} />
	<ImportCsvModal
		open={showImportModal}
		{sciId}
		onClose={() => showImportModal = false}
		onSuccess={() => { showImportModal = false; loadBiens(); }}
	/>

	{#if deleteTargetBien}
		<ConfirmDeleteModal
			open={confirmingDeleteId != null}
			entityName={deleteTargetBien.adresse ?? 'ce bien'}
			entityType="ce bien"
			warningMessage="Cette action supprimera définitivement ce bien immobilier ainsi que tous ses baux, loyers, charges et documents associés. Cette action est irréversible."
			loading={deletingId != null}
			onConfirm={() => { if (deleteTargetBien) handleDeleteBien(deleteTargetBien); }}
			onCancel={() => { confirmingDeleteId = null; }}
		/>
	{/if}
</section>
