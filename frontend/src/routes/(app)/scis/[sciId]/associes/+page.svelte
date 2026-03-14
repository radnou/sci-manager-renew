<script lang="ts">
	import { page } from '$app/state';
	import { getContext } from 'svelte';
	import type { SCIDetail, Associe } from '$lib/api';
	import { fetchSciAssociesList, deleteAssocie } from '$lib/api';
	import { addToast } from '$lib/components/ui/toast';
	import RoleGate from '$lib/components/RoleGate.svelte';
	import { UserPlus, Pencil, Trash2, Loader2 } from 'lucide-svelte';
	import AssocieModal from '$lib/components/fiche-bien/modals/AssocieModal.svelte';

	const sci = getContext<SCIDetail>('sci');
	const userRole = getContext<string>('userRole');

	let sciId = $derived(page.params.sciId!);
	let isGerant = $derived(userRole === 'gerant');
	let showAssocieModal = $state(false);
	let editingAssocie: Associe | null = $state(null);

	let associes: Associe[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);
	let deletingId: string | null = $state(null);
	let confirmingDeleteId: string | null = $state(null);

	$effect(() => {
		if (sciId) {
			loadAssocies();
		}
	});

	async function loadAssocies() {
		loading = true;
		error = null;
		try {
			associes = await fetchSciAssociesList(sciId);
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger les associés.';
			associes = [];
		} finally {
			loading = false;
		}
	}

	const roleBadge: Record<string, { label: string; class: string }> = {
		gerant: {
			label: 'Gérant',
			class: 'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300'
		},
		associe: {
			label: 'Associé',
			class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
		}
	};

	function getRoleBadge(role: string | null | undefined) {
		if (!role) return roleBadge['associe'];
		return roleBadge[role] ?? roleBadge['associe'];
	}

	function handleEditAssocie(associe: Associe) {
		editingAssocie = associe;
		showAssocieModal = true;
	}

	async function handleDeleteAssocie(associe: Associe) {
		deletingId = String(associe.id);
		try {
			await deleteAssocie(associe.id);
			addToast({ title: 'Associé supprimé', description: `${associe.nom} a été retiré.`, variant: 'success' });
			await loadAssocies();
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? "Impossible de supprimer l'associé.", variant: 'error' });
		} finally {
			deletingId = null;
			confirmingDeleteId = null;
		}
	}
</script>

<svelte:head><title>Associés | {sci.nom} | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<div class="flex items-center justify-between">
			<h1 class="sci-page-title">Associés</h1>
			{#if isGerant}
				<button
					onclick={() => { editingAssocie = null; showAssocieModal = true; }}
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				>
					<UserPlus class="h-4 w-4" />
					Ajouter un associé
				</button>
			{/if}
		</div>
	</header>

	{#if loading}
		<div class="sci-loading" aria-label="Chargement"></div>
	{:else if error}
		<div
			class="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30"
		>
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={loadAssocies}
				class="mt-3 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				Réessayer
			</button>
		</div>
	{:else if associes.length > 0}
		<div class="sci-stagger space-y-3">
			{#each associes as associe (String(associe.id))}
				{@const isOnlyGerant = associe.role === 'gerant' && associes.filter(x => x.role === 'gerant').length <= 1}
				<div
					class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950"
				>
					<div class="flex items-center justify-between">
						<div>
							<p class="font-medium text-slate-900 dark:text-slate-100">
								{associe.nom}
							</p>
							{#if associe.email}
								<p class="text-sm text-slate-500 dark:text-slate-400">
									{associe.email}
								</p>
							{/if}
						</div>
						<div class="flex items-center gap-2">
							<span
								class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {getRoleBadge(associe.role).class}"
							>
								{getRoleBadge(associe.role).label}
							</span>
							<span
								class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300"
							>
								{associe.part ?? 0}%
							</span>
							{#if associe.nb_parts != null}
								<span
									class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300"
								>
									{associe.nb_parts} parts
								</span>
							{/if}
							{#if isGerant}
								<button
									onclick={() => handleEditAssocie(associe)}
									class="ml-1 text-slate-400 transition-colors hover:text-sky-600 dark:hover:text-sky-400"
									aria-label="Modifier l'associé {associe.nom || associe.email}"
									title="Modifier l'associé {associe.nom || associe.email}"
								>
									<Pencil class="h-4 w-4" />
								</button>
								<button
									onclick={() => { confirmingDeleteId = String(associe.id); }}
									disabled={isOnlyGerant || deletingId === String(associe.id)}
									class="ml-1 text-slate-400 transition-colors hover:text-rose-600 disabled:opacity-50 dark:hover:text-rose-400"
									aria-label="Supprimer l'associé {associe.nom || associe.email}"
									title={isOnlyGerant ? 'Impossible de supprimer le seul gérant' : `Supprimer l'associé ${associe.nom || associe.email}`}
								>
									{#if deletingId === String(associe.id)}
										<Loader2 class="h-4 w-4 animate-spin" />
									{:else}
										<Trash2 class="h-4 w-4" />
									{/if}
								</button>
							{/if}
						</div>
					</div>
					{#if confirmingDeleteId === String(associe.id)}
						<div class="mt-3 flex items-center justify-between rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 dark:border-rose-800 dark:bg-rose-950/30">
							<p class="text-sm text-rose-700 dark:text-rose-300">Supprimer l'associé {associe.nom} ?</p>
							<div class="flex items-center gap-2">
								<button
									onclick={() => { confirmingDeleteId = null; }}
									class="rounded-md px-3 py-1 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
								>
									Annuler
								</button>
								<button
									onclick={() => handleDeleteAssocie(associe)}
									disabled={deletingId === String(associe.id)}
									class="inline-flex items-center gap-1.5 rounded-md bg-rose-600 px-3 py-1 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50"
								>
									{#if deletingId === String(associe.id)}
										<Loader2 class="h-3.5 w-3.5 animate-spin" />
									{/if}
									Confirmer
								</button>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
		{#if associes.length > 0}
			{@const totalParts = associes.reduce((sum: number, a: Associe) => sum + (a.part || 0), 0)}
			<div class="mt-4 p-3 rounded-lg border {Math.abs(totalParts - 100) < 0.01 ? 'border-emerald-300 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-950' : 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-950'}">
				<span class="text-sm font-medium">Total des parts : {totalParts.toFixed(2)}%</span>
				{#if Math.abs(totalParts - 100) >= 0.01}
					<span class="text-sm text-red-600 dark:text-red-400 ml-2">La somme doit être égale à 100%</span>
				{/if}
			</div>
			{@const totalNbParts = associes.reduce((sum: number, a: Associe) => sum + (a.nb_parts ?? 0), 0)}
			{#if totalNbParts > 0}
				<div class="mt-2 p-3 rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-900">
					<span class="text-sm font-medium">Nombre de parts : {totalNbParts}{#if sci.nb_parts_total != null} / {sci.nb_parts_total}{/if}</span>
				</div>
			{/if}
		{/if}
	{:else}
		<div
			class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
		>
			<p class="text-sm text-slate-500 dark:text-slate-400">Aucun associé.</p>
			{#if isGerant}
				<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
					Cliquez sur "Ajouter un associé" pour ajouter un membre.
				</p>
			{/if}
		</div>
	{/if}

	<AssocieModal bind:open={showAssocieModal} {sciId} associe={editingAssocie} onSuccess={() => { editingAssocie = null; loadAssocies(); }} />
</section>
