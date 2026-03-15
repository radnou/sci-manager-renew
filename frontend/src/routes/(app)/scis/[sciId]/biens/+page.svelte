<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import type { SCIDetail, Bien, SubscriptionEntitlements } from '$lib/api';
	import { fetchSciBiensList, deleteBien, fetchSubscriptionEntitlements } from '$lib/api';

	type BienListItem = Bien & {
		statut?: string | null;
		bail_actif?: unknown;
	};
	import { formatEur } from '$lib/high-value/formatters';
	import { MapPin, Plus, LayoutGrid, List, Pencil, Trash2, Receipt, Loader2, TrendingUp, Wallet, ArrowUpRight, Upload } from 'lucide-svelte';
	import BienModal from '$lib/components/fiche-bien/modals/BienModal.svelte';
	import ImportCsvModal from '$lib/components/ImportCsvModal.svelte';
	import { addToast } from '$lib/components/ui/toast';

	const sci = getContext<SCIDetail>('sci');
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
		loue: 'Loué',
		vacant: 'Vacant',
		travaux: 'Travaux'
	};

	function getStatut(bien: BienListItem): string {
		return bien.statut || (bien.bail_actif ? 'loue' : 'vacant');
	}
</script>

<svelte:head><title>Biens | {sci.nom} | GererSCI</title></svelte:head>

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

				{#if isGerant}
					<button
						onclick={() => showImportModal = true}
						class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
					>
						<Upload class="h-4 w-4" />
						Importer (CSV)
					</button>
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
				{/if}
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
				<div
					class="group rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700"
				>
					<!-- Header: address + badge -->
					<div class="flex items-start justify-between gap-2">
						<a
							href="/scis/{sciId}/biens/{bien.id}"
							class="font-semibold text-slate-900 hover:text-sky-600 dark:text-slate-100 dark:hover:text-sky-400"
						>
							{bien.adresse}
						</a>
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
						{#if bien.type_locatif}
							<span class="rounded-full bg-slate-100 px-2 py-0.5 dark:bg-slate-800">
								{bien.type_locatif}
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
					{#if isGerant}
						<div class="mt-4 flex items-center gap-2 border-t border-slate-100 pt-3 dark:border-slate-800">
							<a
								href="/scis/{sciId}/biens/{bien.id}"
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
								href="/scis/{sciId}/biens/{bien.id}#loyers"
								class="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-sky-600 transition-colors hover:bg-sky-50 hover:text-sky-700 dark:text-sky-400 dark:hover:bg-sky-950/30 dark:hover:text-sky-300"
							>
								<Receipt class="h-3.5 w-3.5" />
								Quittance
							</a>
						</div>
						{#if confirmingDeleteId != null && bien.id != null && confirmingDeleteId === String(bien.id)}
							<div class="mt-3 flex items-center justify-between rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 dark:border-rose-800 dark:bg-rose-950/30">
								<p class="text-sm text-rose-700 dark:text-rose-300">Supprimer "{bien.adresse}" ?</p>
								<div class="flex items-center gap-2">
									<button
										onclick={() => { confirmingDeleteId = null; }}
										class="rounded-md px-3 py-1 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
									>
										Annuler
									</button>
									<button
										onclick={() => handleDeleteBien(bien)}
										disabled={isDeleting}
										class="inline-flex items-center gap-1.5 rounded-md bg-rose-600 px-3 py-1 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50"
									>
										{#if isDeleting}
											<Loader2 class="h-3.5 w-3.5 animate-spin" />
										{/if}
										Confirmer
									</button>
								</div>
							</div>
						{/if}
					{/if}
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
						{#if isGerant}
							<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Actions</th>
						{/if}
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100 dark:divide-slate-800">
					{#each biens as bien (bien.id)}
						{@const statut = getStatut(bien)}
						{@const badgeClass = statutBadge[statut] ?? statutBadge['vacant']}
						{@const label = statutLabel[statut] ?? statut}
						{@const isDeleting = deletingId != null && bien.id != null && deletingId === String(bien.id)}
						<tr class="transition-colors hover:bg-slate-50 dark:hover:bg-slate-900/50">
							<td class="px-4 py-3">
								<a
									href="/scis/{sciId}/biens/{bien.id}"
									class="font-medium text-slate-900 hover:text-sky-600 dark:text-slate-100 dark:hover:text-sky-400"
								>
									{bien.adresse}
								</a>
							</td>
							<td class="whitespace-nowrap px-4 py-3 text-slate-500 dark:text-slate-400">
								{bien.ville ?? '--'} {bien.code_postal ?? ''}
							</td>
							<td class="whitespace-nowrap px-4 py-3">
								{#if bien.type_locatif}
									<span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs dark:bg-slate-800 dark:text-slate-300">
										{bien.type_locatif}
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
							{#if isGerant}
								<td class="whitespace-nowrap px-4 py-3">
									<div class="flex items-center gap-1">
										<a
											href="/scis/{sciId}/biens/{bien.id}"
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
											href="/scis/{sciId}/biens/{bien.id}#loyers"
											class="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-sky-50 hover:text-sky-600 dark:hover:bg-sky-950/30 dark:hover:text-sky-400"
											title="Quittance"
											aria-label="Quittance {bien.adresse}"
										>
											<Receipt class="h-4 w-4" />
										</a>
									</div>
								</td>
							{/if}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		{#if confirmingDeleteId}
			{@const bienToDelete = biens.find(b => b.id != null && String(b.id) === confirmingDeleteId)}
			{#if bienToDelete}
				<div class="mt-3 flex items-center justify-between rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 dark:border-rose-800 dark:bg-rose-950/30">
					<p class="text-sm text-rose-700 dark:text-rose-300">Supprimer "{bienToDelete.adresse}" ? Cette action est irréversible.</p>
					<div class="flex items-center gap-2">
						<button
							onclick={() => { confirmingDeleteId = null; }}
							class="rounded-md px-3 py-1 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
						>
							Annuler
						</button>
						<button
							onclick={() => handleDeleteBien(bienToDelete)}
							disabled={deletingId != null && bienToDelete.id != null && deletingId === String(bienToDelete.id)}
							class="inline-flex items-center gap-1.5 rounded-md bg-rose-600 px-3 py-1 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50"
						>
							{#if deletingId != null && bienToDelete.id != null && deletingId === String(bienToDelete.id)}
								<Loader2 class="h-3.5 w-3.5 animate-spin" />
							{/if}
							Confirmer
						</button>
					</div>
				</div>
			{/if}
		{/if}
	{/if}

	<BienModal bind:open={showBienModal} {sciId} />
	<ImportCsvModal
		open={showImportModal}
		{sciId}
		onClose={() => showImportModal = false}
		onSuccess={() => { showImportModal = false; loadBiens(); }}
	/>
</section>
