<script lang="ts">
	import type { FraisAgenceEmbed } from '$lib/api';
	import { deleteFraisForBien } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { Building2, Plus, Trash2, Pencil, X } from 'lucide-svelte';
	import FraisModal from '$lib/components/fiche-bien/modals/FraisModal.svelte';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import {
		announceFicheBienModal,
		subscribeExclusiveFicheBienModal
	} from '$lib/components/fiche-bien/modal-coordinator';

	interface Props {
		fraisAgence: FraisAgenceEmbed[];
		isGerant: boolean;
		sciId: string;
		bienId: string | number;
		onRefresh: () => void;
	}

	let { fraisAgence = $bindable(), isGerant, sciId, bienId, onRefresh }: Props = $props();

	let showFraisModal = $state(false);
	let showDetails = $state(false);

	$effect(() => subscribeExclusiveFicheBienModal('frais', () => { showFraisModal = false; }));
	$effect(() => subscribeExclusiveFicheBienModal('agence', () => { showDetails = false; }));

	const typeFraisLabels: Record<string, string> = {
		gestion_locative: 'Gestion locative',
		mise_en_location: 'Mise en location',
		autre: 'Autre'
	};

	function getFraisLabel(type: string): string {
		return typeFraisLabels[type] ?? type;
	}

	function openFraisModal() {
		announceFicheBienModal('frais');
		showFraisModal = true;
	}

	function toggleDetails() {
		if (showDetails) {
			showDetails = false;
		} else {
			announceFicheBienModal('agence');
			showDetails = true;
		}
	}

	// Derive agency summary from frais list
	const agencySummary = $derived.by(() => {
		if (fraisAgence.length === 0) return null;
		const totalFrais = fraisAgence.reduce((sum, f) => sum + Number(f.montant ?? 0), 0);
		const byType = new Map<string, number>();
		for (const f of fraisAgence) {
			byType.set(f.type_frais, (byType.get(f.type_frais) ?? 0) + Number(f.montant ?? 0));
		}
		const primaryType = [...byType.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'gestion_locative';
		return { totalFrais, count: fraisAgence.length, primaryType };
	});

	function handleDeleteFrais(fraisId: number) {
		const item = fraisAgence.find(f => f.id === fraisId);
		if (!item) return;
		fraisAgence = fraisAgence.filter(f => f.id !== fraisId);
		addToast({
			title: 'Frais supprimés',
			variant: 'undo',
			undoCallbacks: {
				onUndo: () => {
					fraisAgence = [...fraisAgence, item].sort((a, b) => a.id - b.id);
				},
				onExpire: async () => {
					try {
						await deleteFraisForBien(sciId, bienId, fraisId);
						onRefresh();
					} catch (err: any) {
						addToast({ title: err?.message ?? 'Erreur suppression', variant: 'error' });
						onRefresh();
					}
				}
			}
		});
	}
</script>

<div class="space-y-6">
	<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="mb-4 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<Building2 class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Agence de gestion</h2>
			</div>
			{#if isGerant}
				<button
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
					onclick={openFraisModal}
				>
					<Plus class="h-4 w-4" />
					Ajouter des frais
				</button>
			{/if}
		</div>

		{#if fraisAgence.length === 0}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
			>
				<Building2 class="mb-3 h-10 w-10 text-slate-300 dark:text-slate-600" />
				<p class="text-sm font-medium text-slate-500 dark:text-slate-400">
					Aucune agence de gestion.
				</p>
				<p class="mt-1 max-w-sm text-center text-xs text-slate-400 dark:text-slate-500">
					Ajoutez une agence pour suivre les frais de mandat.
				</p>
				{#if isGerant}
					<button
						onclick={openFraisModal}
						class="mt-4 inline-flex items-center gap-2 rounded-lg border border-sky-200 bg-sky-50 px-4 py-2 text-sm font-medium text-sky-700 transition-colors hover:bg-sky-100 dark:border-sky-800 dark:bg-sky-950/30 dark:text-sky-400 dark:hover:bg-sky-900/40"
					>
						<Plus class="h-4 w-4" />
						Ajouter une agence de gestion
					</button>
				{/if}
			</div>
		{:else}
			{#if agencySummary}
				<div class="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-5 dark:border-slate-700 dark:from-slate-900 dark:to-slate-950">
					<div class="flex items-start justify-between gap-4">
						<div class="flex items-start gap-4">
							<div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-sky-100 dark:bg-sky-900/40">
								<Building2 class="h-6 w-6 text-sky-600 dark:text-sky-400" />
							</div>
							<div>
								<p class="text-base font-semibold text-slate-900 dark:text-slate-100">
									Mandat de {getFraisLabel(agencySummary.primaryType).toLowerCase()}
								</p>
								<p class="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
									{agencySummary.count} frais enregistré{agencySummary.count > 1 ? 's' : ''}
								</p>
							</div>
						</div>
						{#if isGerant}
							<button
								onclick={toggleDetails}
								class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
							>
								{#if showDetails}
									<X class="h-3.5 w-3.5" />
									Fermer
								{:else}
									<Pencil class="h-3.5 w-3.5" />
									Détails
								{/if}
							</button>
						{/if}
					</div>

					<div class="mt-4 grid gap-3 sm:grid-cols-2">
						<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
							<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Total frais</p>
							<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{formatEur(agencySummary.totalFrais)}</p>
						</div>
						<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
							<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Type principal</p>
							<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{getFraisLabel(agencySummary.primaryType)}</p>
						</div>
					</div>
				</div>
			{/if}

			{#if showDetails}
				<div class="mt-4 overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
					<table class="w-full text-left text-sm">
						<thead>
							<tr class="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-900">
								<th class="px-4 pb-3 pt-3 text-xs font-medium text-slate-500">Type</th>
								<th class="px-4 pb-3 pt-3 text-xs font-medium text-slate-500">Montant</th>
								<th class="px-4 pb-3 pt-3 text-xs font-medium text-slate-500">Date</th>
								<th class="px-4 pb-3 pt-3 text-xs font-medium text-slate-500">Description</th>
								{#if isGerant}
									<th class="px-4 pb-3 pt-3 text-xs font-medium text-slate-500">Actions</th>
								{/if}
							</tr>
						</thead>
						<tbody>
							{#each fraisAgence as frais (frais.id)}
								<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
									<td class="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
										{getFraisLabel(frais.type_frais)}
									</td>
									<td class="px-4 py-3 text-slate-700 dark:text-slate-300">
										{formatEur(frais.montant)}
									</td>
									<td class="px-4 py-3 text-slate-500 dark:text-slate-400">
										{formatFrDate(frais.date_frais)}
									</td>
									<td class="px-4 py-3 text-slate-500 dark:text-slate-400">
										{frais.description ?? '—'}
									</td>
									{#if isGerant}
										<td class="px-4 py-3">
											<button
												class="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-2.5 py-1.5 text-xs font-medium text-rose-700 transition-colors hover:bg-rose-100 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-400"
												title="Supprimer"
												onclick={() => handleDeleteFrais(frais.id)}
											>
												<Trash2 class="h-3 w-3" />
												Supprimer
											</button>
										</td>
									{/if}
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{/if}
	</div>
	<FraisModal bind:open={showFraisModal} {sciId} {bienId} onSuccess={onRefresh} />
</div>
