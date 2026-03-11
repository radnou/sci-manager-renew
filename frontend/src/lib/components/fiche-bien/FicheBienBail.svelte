<script lang="ts">
	import type { BailEmbed } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { Plus, Pencil, Users, Calendar, History } from 'lucide-svelte';
	import BailModal from '$lib/components/fiche-bien/modals/BailModal.svelte';

	interface Props {
		bail: BailEmbed | null;
		isGerant: boolean;
		sciId: string;
		bienId: string | number;
		onRefresh: () => void;
	}

	let { bail, isGerant, sciId, bienId, onRefresh }: Props = $props();

	let showBailModal = $state(false);
	let editBail: BailEmbed | null = $state(null);

	const statutConfig: Record<string, { label: string; class: string }> = {
		en_cours: {
			label: 'En cours',
			class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
		},
		expire: {
			label: 'Expiré',
			class: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
		},
		resilie: {
			label: 'Résilié',
			class: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
		}
	};

	function getStatut(statut: string | null | undefined) {
		if (!statut) return statutConfig['en_cours'];
		return (
			statutConfig[statut] ?? {
				label: statut,
				class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
			}
		);
	}
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Bail</h2>
		<div class="flex items-center gap-2">
			<a
				href="/scis/{sciId}/biens/{bienId}/baux"
				class="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
			>
				<History class="h-4 w-4" />
				Historique
			</a>
			{#if isGerant && !bail}
				<button
					onclick={() => { editBail = null; showBailModal = true; }}
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				>
					<Plus class="h-4 w-4" />
					Créer un bail
				</button>
			{/if}
		</div>
	</div>

	{#if !bail}
		<div
			class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
		>
			<Users class="mb-3 h-8 w-8 text-slate-400 dark:text-slate-500" />
			<p class="text-sm text-slate-500 dark:text-slate-400">Aucun bail actif pour ce bien.</p>
			{#if isGerant}
				<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
					Cliquez sur "Créer un bail" pour commencer.
				</p>
			{/if}
		</div>
	{:else}
		{@const statut = getStatut(bail.statut)}
		<div class="space-y-4">
			<!-- Statut badge + modify button -->
			<div class="flex items-center justify-between">
				<span
					class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {statut.class}"
				>
					{statut.label}
				</span>
				{#if isGerant}
					<button
						onclick={() => { editBail = bail; showBailModal = true; }}
						class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
					>
						<Pencil class="h-3.5 w-3.5" />
						Modifier
					</button>
				{/if}
			</div>

			<!-- Locataires -->
			<div>
				<p
					class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
				>
					{bail.locataires.length > 1 ? 'Locataires (colocation)' : 'Locataire'}
				</p>
				<div class="mt-1.5 flex flex-wrap gap-2">
					{#if bail.locataires.length === 0}
						<span class="text-sm text-slate-400">Aucun locataire rattaché</span>
					{:else}
						{#each bail.locataires as loc (loc.id)}
							<span
								class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
							>
								<Users class="h-3.5 w-3.5 text-slate-400" />
								{loc.prenom ? `${loc.prenom} ${loc.nom}` : loc.nom}
							</span>
						{/each}
					{/if}
				</div>
			</div>

			<!-- Dates -->
			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<p
						class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
					>
						Date de début
					</p>
					<p class="mt-1 flex items-center gap-1.5 text-sm font-medium text-slate-900 dark:text-slate-100">
						<Calendar class="h-3.5 w-3.5 text-slate-400" />
						{formatFrDate(bail.date_debut)}
					</p>
				</div>
				<div>
					<p
						class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
					>
						Date de fin
					</p>
					<p class="mt-1 flex items-center gap-1.5 text-sm font-medium text-slate-900 dark:text-slate-100">
						<Calendar class="h-3.5 w-3.5 text-slate-400" />
						{bail.date_fin ? formatFrDate(bail.date_fin) : 'Indéterminée'}
					</p>
				</div>
			</div>

			<!-- Montants -->
			<div class="grid gap-4 sm:grid-cols-3">
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p
						class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
					>
						Loyer HC
					</p>
					<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
						{formatEur(bail.loyer_hc)}
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p
						class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
					>
						Provisions charges
					</p>
					<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
						{formatEur(bail.charges_provisions)}
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p
						class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
					>
						Dépôt de garantie
					</p>
					<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
						{formatEur(bail.depot_garantie)}
					</p>
				</div>
			</div>

			<!-- Indice de révision -->
			{#if bail.revision_indice}
				<div>
					<p
						class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
					>
						Indice de révision
					</p>
					<p class="mt-1 text-sm font-medium text-slate-900 dark:text-slate-100">
						{bail.revision_indice}
					</p>
				</div>
			{/if}
		</div>
	{/if}

	<BailModal bind:open={showBailModal} {sciId} bienId={bienId} editItem={editBail} onSuccess={onRefresh} />
</div>
