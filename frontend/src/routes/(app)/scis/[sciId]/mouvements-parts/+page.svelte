<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';
	import { fetchMouvementsParts, createMouvementParts, deleteMouvementParts } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { ArrowLeftRight, Plus, Trash2, Loader2 } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');

	let mouvements: any[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);
	let showCreateForm = $state(false);
	let creating = $state(false);
	let deletingId: string | null = $state(null);

	const userRole = getContext<string>('userRole');
	const isGerant = $derived(userRole === 'gerant');

	// Form fields
	let newDate = $state('');
	let newType = $state('cession');
	let newCedant = $state('');
	let newCessionnaire = $state('');
	let newNbParts = $state(0);
	let newPrixTotal = $state(0);

	$effect(() => {
		loadData();
	});

	async function loadData() {
		loading = true;
		error = null;
		try {
			mouvements = await fetchMouvementsParts(sci.id);
		} catch (err: any) {
			error = 'Impossible de charger les mouvements de parts.';
		} finally {
			loading = false;
		}
	}

	async function handleCreate() {
		if (!newDate || !newCedant || !newCessionnaire || newNbParts <= 0) {
			addToast({
				title: 'Champs requis',
				description: 'Veuillez remplir tous les champs obligatoires.',
				variant: 'error'
			});
			return;
		}
		creating = true;
		try {
			await createMouvementParts(sci.id, {
				date_mouvement: newDate,
				type_mouvement: newType,
				cedant: newCedant,
				cessionnaire: newCessionnaire,
				nb_parts: newNbParts,
				prix_total: newPrixTotal
			});
			addToast({
				title: 'Mouvement enregistre',
				description: 'Le mouvement de parts a ete cree.',
				variant: 'success'
			});
			showCreateForm = false;
			resetForm();
			await loadData();
		} catch (err: any) {
			addToast({
				title: 'Erreur',
				description: err?.message ?? 'Impossible de creer le mouvement.',
				variant: 'error'
			});
		} finally {
			creating = false;
		}
	}

	async function handleDelete(mouvement: any) {
		if (!mouvement.id) return;
		deletingId = String(mouvement.id);
		try {
			await deleteMouvementParts(sci.id, mouvement.id);
			addToast({
				title: 'Mouvement supprime',
				description: 'Le mouvement a ete supprime.',
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
		newType = 'cession';
		newCedant = '';
		newCessionnaire = '';
		newNbParts = 0;
		newPrixTotal = 0;
	}
</script>

<svelte:head><title>Mouvements de parts | {sci.nom} | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<h1 class="sci-page-title">Mouvements de parts</h1>
	</header>

	<div
		class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
	>
		<div class="mb-4 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<ArrowLeftRight class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
					Registre des mouvements
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
					Enregistrer un mouvement
				</button>
			{/if}
		</div>

		{#if showCreateForm}
			<div
				class="mb-4 rounded-xl border border-sky-200 bg-sky-50/50 p-4 dark:border-sky-800 dark:bg-sky-950/20"
			>
				<p class="mb-3 text-sm font-medium text-slate-900 dark:text-slate-100">
					Nouveau mouvement de parts
				</p>
				<div class="grid gap-3 sm:grid-cols-3">
					<div>
						<label for="mv-date" class="block text-xs font-medium text-slate-500 uppercase"
							>Date</label
						>
						<input
							id="mv-date"
							type="date"
							bind:value={newDate}
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
					<div>
						<label for="mv-type" class="block text-xs font-medium text-slate-500 uppercase"
							>Type</label
						>
						<select
							id="mv-type"
							bind:value={newType}
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						>
							<option value="cession">Cession</option>
							<option value="donation">Donation</option>
							<option value="succession">Succession</option>
							<option value="apport">Apport</option>
						</select>
					</div>
					<div>
						<label for="mv-cedant" class="block text-xs font-medium text-slate-500 uppercase"
							>Cedant</label
						>
						<input
							id="mv-cedant"
							type="text"
							bind:value={newCedant}
							placeholder="Nom du cedant"
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
					<div>
						<label for="mv-cessionnaire" class="block text-xs font-medium text-slate-500 uppercase"
							>Cessionnaire</label
						>
						<input
							id="mv-cessionnaire"
							type="text"
							bind:value={newCessionnaire}
							placeholder="Nom du cessionnaire"
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
					<div>
						<label for="mv-nbparts" class="block text-xs font-medium text-slate-500 uppercase"
							>Nb parts</label
						>
						<input
							id="mv-nbparts"
							type="number"
							min="1"
							bind:value={newNbParts}
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
					<div>
						<label for="mv-prix" class="block text-xs font-medium text-slate-500 uppercase"
							>Prix total</label
						>
						<input
							id="mv-prix"
							type="number"
							min="0"
							step="0.01"
							bind:value={newPrixTotal}
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
						Enregistrer
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
		{:else if mouvements.length === 0}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
			>
				<ArrowLeftRight class="mb-2 h-8 w-8 text-slate-300 dark:text-slate-600" />
				<p class="text-sm text-slate-500 dark:text-slate-400">
					Aucun mouvement de parts enregistre.
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
								>Cedant</th
							>
							<th
								class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Cessionnaire</th
							>
							<th
								class="pb-3 pr-4 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Nb parts</th
							>
							<th
								class="pb-3 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Prix total</th
							>
							{#if isGerant}
								<th class="pb-3 w-10"></th>
							{/if}
						</tr>
					</thead>
					<tbody>
						{#each mouvements as mv (mv.id)}
							<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
								<td class="py-3 pr-4 text-slate-900 dark:text-slate-100">
									{formatFrDate(mv.date_mouvement)}
								</td>
								<td class="py-3 pr-4">
									<span
										class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize
										{mv.type_mouvement === 'cession'
											? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
											: mv.type_mouvement === 'donation'
												? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
												: mv.type_mouvement === 'succession'
													? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
													: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'}"
									>
										{mv.type_mouvement}
									</span>
								</td>
								<td class="py-3 pr-4 text-slate-700 dark:text-slate-300">{mv.cedant}</td>
								<td class="py-3 pr-4 text-slate-700 dark:text-slate-300"
									>{mv.cessionnaire}</td
								>
								<td
									class="py-3 pr-4 text-right font-semibold text-slate-900 dark:text-slate-100"
									>{mv.nb_parts}</td
								>
								<td class="py-3 text-right text-slate-700 dark:text-slate-300">
									{formatEur(mv.prix_total)}
								</td>
								{#if isGerant}
									<td class="py-3 text-right">
										<button
											onclick={() => handleDelete(mv)}
											disabled={deletingId === String(mv.id)}
											class="text-slate-400 transition-colors hover:text-rose-600 disabled:opacity-50 dark:hover:text-rose-400"
											title="Supprimer ce mouvement"
										>
											{#if deletingId === String(mv.id)}
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
