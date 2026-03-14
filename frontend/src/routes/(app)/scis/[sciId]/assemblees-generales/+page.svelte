<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';
	import {
		fetchAssembleesGenerales,
		createAssembleeGenerale,
		deleteAssembleeGenerale
	} from '$lib/api';
	import { formatFrDate } from '$lib/high-value/formatters';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { Users, Plus, Trash2, Loader2, Download } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');

	let assemblees: any[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);
	let showCreateForm = $state(false);
	let creating = $state(false);
	let deletingId: string | null = $state(null);

	const userRole = getContext<string>('userRole');
	const isGerant = $derived(userRole === 'gerant');

	// Form fields
	let newDate = $state('');
	let newType = $state('ordinaire');
	let newExercice = $state(new Date().getFullYear() - 1);
	let newOrdreJour = $state('');

	$effect(() => {
		loadData();
	});

	async function loadData() {
		loading = true;
		error = null;
		try {
			assemblees = await fetchAssembleesGenerales(sci.id);
		} catch (err: any) {
			error = 'Impossible de charger les assemblees generales.';
		} finally {
			loading = false;
		}
	}

	async function handleCreate() {
		if (!newDate) {
			addToast({
				title: 'Champs requis',
				description: 'Veuillez renseigner la date de l\'assemblee.',
				variant: 'error'
			});
			return;
		}
		creating = true;
		try {
			await createAssembleeGenerale(sci.id, {
				date_assemblee: newDate,
				type_assemblee: newType,
				exercice: newExercice,
				ordre_du_jour: newOrdreJour || null
			});
			addToast({
				title: 'AG enregistree',
				description: 'L\'assemblee generale a ete creee.',
				variant: 'success'
			});
			showCreateForm = false;
			resetForm();
			await loadData();
		} catch (err: any) {
			addToast({
				title: 'Erreur',
				description: err?.message ?? 'Impossible de creer l\'AG.',
				variant: 'error'
			});
		} finally {
			creating = false;
		}
	}

	async function handleDelete(ag: any) {
		if (!ag.id) return;
		deletingId = String(ag.id);
		try {
			await deleteAssembleeGenerale(sci.id, ag.id);
			addToast({
				title: 'AG supprimee',
				description: 'L\'assemblee generale a ete supprimee.',
				variant: 'success'
			});
			await loadData();
		} catch (err: any) {
			addToast({
				title: 'Erreur',
				description: err?.message ?? 'Impossible de supprimer.',
				variant: 'error'
			});
		} finally {
			deletingId = null;
		}
	}

	function resetForm() {
		newDate = '';
		newType = 'ordinaire';
		newExercice = new Date().getFullYear() - 1;
		newOrdreJour = '';
	}

	function formatQuorum(value: number | null | undefined): string {
		if (value == null) return '--';
		return `${value}%`;
	}

	function typeLabel(type: string): string {
		if (type === 'ordinaire') return 'Ordinaire';
		if (type === 'extraordinaire') return 'Extraordinaire';
		return type;
	}

	function typeBadgeClass(type: string): string {
		if (type === 'ordinaire') {
			return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
		}
		if (type === 'extraordinaire') {
			return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400';
		}
		return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
	}
</script>

<svelte:head><title>Assemblees generales | {sci.nom} | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<h1 class="sci-page-title">Assemblees generales</h1>
	</header>

	<div
		class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
	>
		<div class="mb-4 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<Users class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
					Registre des AG
				</h2>
			</div>
			{#if isGerant}
				<button
					onclick={() => {
						showCreateForm = !showCreateForm;
					}}
					class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
				>
					<Plus class="h-4 w-4" />
					Nouvelle AG
				</button>
			{/if}
		</div>

		{#if showCreateForm}
			<div
				class="mb-4 rounded-xl border border-sky-200 bg-sky-50/50 p-4 dark:border-sky-800 dark:bg-sky-950/20"
			>
				<p class="mb-3 text-sm font-medium text-slate-900 dark:text-slate-100">
					Nouvelle assemblee generale
				</p>
				<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
					<div>
						<label for="ag-date" class="block text-xs font-medium text-slate-500 uppercase"
							>Date</label
						>
						<input
							id="ag-date"
							type="date"
							bind:value={newDate}
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
					<div>
						<label for="ag-type" class="block text-xs font-medium text-slate-500 uppercase"
							>Type</label
						>
						<select
							id="ag-type"
							bind:value={newType}
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						>
							<option value="ordinaire">Ordinaire</option>
							<option value="extraordinaire">Extraordinaire</option>
						</select>
					</div>
					<div>
						<label for="ag-exercice" class="block text-xs font-medium text-slate-500 uppercase"
							>Exercice</label
						>
						<input
							id="ag-exercice"
							type="number"
							min="2000"
							max="2100"
							bind:value={newExercice}
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
					<div>
						<label for="ag-ordre" class="block text-xs font-medium text-slate-500 uppercase"
							>Ordre du jour</label
						>
						<input
							id="ag-ordre"
							type="text"
							bind:value={newOrdreJour}
							placeholder="Approbation des comptes..."
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
				</div>
				<div class="mt-3 flex justify-end gap-2">
					<button
						onclick={() => {
							showCreateForm = false;
						}}
						class="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
					>
						Annuler
					</button>
					<button
						onclick={handleCreate}
						disabled={creating}
						class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
					>
						{#if creating}
							<Loader2 class="h-4 w-4 animate-spin" />
						{/if}
						Creer
					</button>
				</div>
			</div>
		{/if}

		{#if loading}
			<div class="sci-loading" aria-label="Chargement"></div>
		{:else if error}
			<div
				class="rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-900 dark:bg-rose-950/30"
			>
				<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
				<button
					onclick={loadData}
					class="mt-2 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
				>
					Reessayer
				</button>
			</div>
		{:else if assemblees.length === 0}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
			>
				<Users class="mb-2 h-8 w-8 text-slate-300 dark:text-slate-600" />
				<p class="text-sm text-slate-500 dark:text-slate-400">
					Aucune assemblee generale enregistree.
				</p>
			</div>
		{:else}
			<div class="sci-fade-in-up overflow-x-auto">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-slate-200 dark:border-slate-700">
							<th
								class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Date</th
							>
							<th
								class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Type</th
							>
							<th
								class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Exercice</th
							>
							<th
								class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Quorum</th
							>
							<th
								class="pb-3 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>PV</th
							>
							{#if isGerant}
								<th class="pb-3 w-10"></th>
							{/if}
						</tr>
					</thead>
					<tbody>
						{#each assemblees as ag (ag.id)}
							<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
								<td class="py-3 pr-4 text-slate-900 dark:text-slate-100">
									{formatFrDate(ag.date_assemblee)}
								</td>
								<td class="py-3 pr-4">
									<span
										class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium {typeBadgeClass(ag.type_assemblee)}"
									>
										{typeLabel(ag.type_assemblee)}
									</span>
								</td>
								<td class="py-3 pr-4 font-semibold text-slate-900 dark:text-slate-100">
									{ag.exercice}
								</td>
								<td class="py-3 pr-4 text-slate-700 dark:text-slate-300">
									{formatQuorum(ag.quorum)}
								</td>
								<td class="py-3">
									{#if ag.pv_url}
										<a
											href={ag.pv_url}
											target="_blank"
											rel="noopener noreferrer"
											class="inline-flex items-center gap-1 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
										>
											<Download class="h-3.5 w-3.5" />
											Telecharger
										</a>
									{:else}
										<span class="text-sm text-slate-400">--</span>
									{/if}
								</td>
								{#if isGerant}
									<td class="py-3 text-right">
										<button
											onclick={() => handleDelete(ag)}
											disabled={deletingId === String(ag.id)}
											class="text-slate-400 transition-colors hover:text-rose-600 disabled:opacity-50 dark:hover:text-rose-400"
											title="Supprimer cette AG"
										>
											{#if deletingId === String(ag.id)}
												<Loader2 class="h-4 w-4 animate-spin" />
											{:else}
												<Trash2 class="h-4 w-4" />
											{/if}
										</button>
									</td>
								{/if}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</section>
