<script lang="ts">
	import type { BailEmbed, AvenantBailPayload } from '$lib/api';
	import { creerAvenant } from '$lib/api';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { FileSignature, Loader2 } from 'lucide-svelte';

	interface Props {
		showForm: boolean;
		bail: BailEmbed;
		sciId: string;
		bienId: string | number;
		onRefresh: () => void;
	}

	let { showForm = $bindable(), bail, sciId, bienId, onRefresh }: Props = $props();

	let avenantSaving = $state(false);
	let avenantType = $state<AvenantBailPayload['type_avenant']>('revision_loyer');
	let avenantNouvelleValeur = $state('');
	let avenantDateEffet = $state(new Date().toISOString().split('T')[0]);
	let avenantMotif = $state('');

	const avenantTypeOptions: Array<{ value: AvenantBailPayload['type_avenant']; label: string; placeholder: string }> = [
		{ value: 'revision_loyer', label: 'Révision de loyer', placeholder: 'Nouveau loyer HC (ex: 850)' },
		{ value: 'modif_charges', label: 'Modification des charges', placeholder: 'Nouvelles charges (ex: 180)' },
		{ value: 'ajout_locataire', label: 'Ajout de locataire', placeholder: 'Nom du nouveau locataire' },
		{ value: 'autre', label: 'Autre modification', placeholder: 'Détail de la modification' }
	];

	const avenantPlaceholder = $derived(
		avenantTypeOptions.find(o => o.value === avenantType)?.placeholder ?? ''
	);

	async function submitAvenant() {
		if (!bail || !avenantNouvelleValeur.trim() || !avenantDateEffet) return;
		avenantSaving = true;
		try {
			await creerAvenant(sciId, String(bienId), String(bail.id), {
				type_avenant: avenantType,
				nouvelle_valeur: avenantNouvelleValeur,
				date_effet: avenantDateEffet,
				motif: avenantMotif
			});
			addToast({ title: 'Avenant créé', description: 'L\'avenant au bail a été enregistré.', variant: 'success' });
			showForm = false;
			onRefresh();
		} catch {
			addToast({ title: 'Erreur', description: 'Impossible de créer l\'avenant.', variant: 'error' });
		} finally {
			avenantSaving = false;
		}
	}
</script>

{#if showForm}
	<div class="rounded-xl border border-indigo-200 bg-indigo-50/50 p-5 dark:border-indigo-800/50 dark:bg-indigo-950/20">
		<h3 class="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
			<FileSignature class="h-4 w-4 text-indigo-500" />
			Créer un avenant
		</h3>
		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label for="avenant-type" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Type d'avenant</label>
				<select
					id="avenant-type"
					bind:value={avenantType}
					class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
				>
					{#each avenantTypeOptions as opt}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>
			<div>
				<label for="avenant-date" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Date d'effet</label>
				<input
					id="avenant-date"
					type="date"
					bind:value={avenantDateEffet}
					class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
				/>
			</div>
			<div>
				<label for="avenant-valeur" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Nouvelle valeur</label>
				<input
					id="avenant-valeur"
					type="text"
					bind:value={avenantNouvelleValeur}
					placeholder={avenantPlaceholder}
					class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
				/>
			</div>
			<div>
				<label for="avenant-motif" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Motif</label>
				<input
					id="avenant-motif"
					type="text"
					bind:value={avenantMotif}
					placeholder="Motif de l'avenant"
					class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
				/>
			</div>
		</div>
		<div class="mt-4 flex items-center justify-end gap-2">
			<button onclick={() => { showForm = false; }} class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800">
				Annuler
			</button>
			<button
				onclick={submitAvenant}
				disabled={avenantSaving || !avenantNouvelleValeur.trim()}
				class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
			>
				{#if avenantSaving}<Loader2 class="h-4 w-4 animate-spin" />{/if}
				Créer l'avenant
			</button>
		</div>
	</div>
{/if}
