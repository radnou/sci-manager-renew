<script lang="ts">
	import type { AssurancePnoEmbed } from '$lib/api';
	import { createPnoForBien, updatePnoForBien, deletePnoForBien } from '$lib/api';
	import type { PnoCreate, PnoUpdate } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { Shield, Plus, Trash2, X, Pencil, CheckCircle, AlertTriangle } from 'lucide-svelte';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import {
		announceFicheBienModal,
		subscribeExclusiveFicheBienModal
	} from '$lib/components/fiche-bien/modal-coordinator';

	interface Props {
		assurancePno: AssurancePnoEmbed | null;
		isGerant: boolean;
		sciId: string;
		bienId: string | number;
		onRefresh: () => void;
	}

	let { assurancePno = $bindable(), isGerant, sciId, bienId, onRefresh }: Props = $props();

	let showPnoForm = $state(false);
	let pnoLoading = $state(false);
	let pnoAssureur = $state('');
	let pnoNumeroContrat = $state('');
	let pnoPrimeAnnuelle = $state(0);
	let pnoDateDebut = $state('');
	let pnoDateFin = $state('');
	let pnoIsEdit = $derived(!!assurancePno && showPnoForm);

	$effect(() => subscribeExclusiveFicheBienModal('pno', () => { showPnoForm = false; }));

	function openPnoForm(existingItem: AssurancePnoEmbed | null = null) {
		if (existingItem) {
			pnoAssureur = existingItem.assureur;
			pnoNumeroContrat = existingItem.numero_contrat ?? '';
			pnoPrimeAnnuelle = existingItem.prime_annuelle;
			pnoDateDebut = existingItem.date_debut;
			pnoDateFin = existingItem.date_fin ?? '';
		} else {
			pnoAssureur = '';
			pnoNumeroContrat = '';
			pnoPrimeAnnuelle = 0;
			pnoDateDebut = '';
			pnoDateFin = '';
		}
		announceFicheBienModal('pno');
		showPnoForm = true;
	}

	function closePnoForm() {
		showPnoForm = false;
	}

	async function handlePnoSubmit() {
		if (!pnoAssureur || !pnoDateDebut || pnoPrimeAnnuelle < 0) return;
		pnoLoading = true;
		try {
			if (pnoIsEdit && assurancePno) {
				const data: PnoUpdate = {
					assureur: pnoAssureur,
					numero_contrat: pnoNumeroContrat || undefined,
					prime_annuelle: pnoPrimeAnnuelle,
					date_debut: pnoDateDebut,
					date_fin: pnoDateFin || undefined
				};
				await updatePnoForBien(sciId, bienId, assurancePno.id, data);
				addToast({ title: 'Assurance PNO mise à jour', variant: 'success' });
			} else {
				const data: PnoCreate = {
					assureur: pnoAssureur,
					numero_contrat: pnoNumeroContrat || undefined,
					prime_annuelle: pnoPrimeAnnuelle,
					date_debut: pnoDateDebut,
					date_fin: pnoDateFin || undefined
				};
				await createPnoForBien(sciId, bienId, data);
				addToast({ title: 'Assurance PNO ajoutée', variant: 'success' });
			}
			closePnoForm();
			onRefresh();
		} catch (err: any) {
			addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
		} finally {
			pnoLoading = false;
		}
	}

	function handleDeletePno() {
		if (!assurancePno) return;
		const pnoId = assurancePno.id;
		const item = assurancePno;
		assurancePno = null;
		addToast({
			title: 'Assurance PNO supprimée',
			variant: 'undo',
			undoCallbacks: {
				onUndo: () => {
					assurancePno = item;
				},
				onExpire: async () => {
					try {
						await deletePnoForBien(sciId, bienId, pnoId);
						onRefresh();
					} catch (err: any) {
						addToast({ title: err?.message ?? 'Erreur suppression', variant: 'error' });
						onRefresh();
					}
				}
			}
		});
	}

	// Compute validity status
	const pnoStatus = $derived.by(() => {
		if (!assurancePno) return null;
		const now = new Date();
		if (!assurancePno.date_fin) {
			return { valid: true, label: 'Valide (sans échéance définie)', variant: 'info' as const };
		}
		const fin = new Date(assurancePno.date_fin);
		if (fin < now) {
			return { valid: false, label: 'Expirée', variant: 'error' as const };
		}
		const diffMs = fin.getTime() - now.getTime();
		const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
		if (diffDays <= 30) {
			return { valid: true, label: `Expire dans ${diffDays} jour${diffDays > 1 ? 's' : ''}`, variant: 'warning' as const };
		}
		const diffMonths = Math.floor(diffDays / 30);
		return { valid: true, label: `Valide (expire dans ${diffMonths} mois)`, variant: 'success' as const };
	});
</script>

<div class="space-y-6">
	<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="mb-4 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<Shield class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Assurance PNO</h2>
			</div>
			{#if isGerant && !assurancePno && !showPnoForm}
				<button
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
					onclick={() => openPnoForm()}
				>
					<Plus class="h-4 w-4" />
					Ajouter
				</button>
			{/if}
		</div>

		{#if showPnoForm}
			<form
				class="mb-5 rounded-2xl border border-sky-200 bg-sky-50/60 p-4 dark:border-sky-900/60 dark:bg-sky-950/20"
				onsubmit={(event) => {
					event.preventDefault();
					handlePnoSubmit();
				}}
			>
				<div class="mb-3 flex items-start justify-between gap-3">
					<div>
						<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
							{pnoIsEdit ? 'Modifier assurance PNO' : 'Ajouter assurance PNO'}
						</p>
					</div>
					<button
						type="button"
						class="rounded-full border border-slate-300 p-2 text-slate-500 transition-colors hover:bg-white hover:text-slate-900 dark:border-slate-700 dark:hover:bg-slate-900 dark:hover:text-slate-100"
						onclick={closePnoForm}
						aria-label="Fermer le formulaire PNO"
					>
						<X class="h-4 w-4" />
					</button>
				</div>

				<div class="grid gap-4 md:grid-cols-2">
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Compagnie</span>
						<input
							id="pno-assureur"
							type="text"
							bind:value={pnoAssureur}
							required
							placeholder="Ex : MAIF, AXA, Allianz..."
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">N° contrat</span>
						<input
							id="pno-contrat"
							type="text"
							bind:value={pnoNumeroContrat}
							placeholder="Optionnel"
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Prime annuelle (€)</span>
						<input
							id="pno-prime"
							type="number"
							bind:value={pnoPrimeAnnuelle}
							min="0"
							step="0.01"
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Date de début</span>
						<input
							id="pno-date-debut"
							type="date"
							lang="fr"
							bind:value={pnoDateDebut}
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block md:col-span-2">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Date d'échéance</span>
						<input
							id="pno-date-fin"
							type="date"
							lang="fr"
							bind:value={pnoDateFin}
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
				</div>

				<div class="mt-4 flex justify-end gap-2">
					<button
						type="button"
						class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-white dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
						onclick={closePnoForm}
					>
						Annuler
					</button>
					<button
						type="submit"
						disabled={pnoLoading}
						class="rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
					>
						{pnoLoading ? 'Enregistrement…' : pnoIsEdit ? 'Mettre à jour' : 'Ajouter'}
					</button>
				</div>
			</form>
		{/if}

		{#if assurancePno}
			<div class="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-5 dark:border-slate-700 dark:from-slate-900 dark:to-slate-950">
				<div class="grid gap-5 sm:grid-cols-2">
					<div>
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Compagnie</p>
						<p class="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{assurancePno.assureur}
						</p>
					</div>
					<div>
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">N° contrat</p>
						<p class="mt-1 text-sm text-slate-700 dark:text-slate-300">
							{assurancePno.numero_contrat ?? '—'}
						</p>
					</div>
					<div>
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Prime annuelle</p>
						<p class="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{formatEur(assurancePno.prime_annuelle)}
						</p>
					</div>
					<div>
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Échéance</p>
						<p class="mt-1 text-sm text-slate-700 dark:text-slate-300">
							{#if assurancePno.date_fin}
								{formatFrDate(assurancePno.date_fin)}
							{:else}
								Sans échéance définie
							{/if}
						</p>
					</div>
				</div>

				<!-- Validity status -->
				{#if pnoStatus}
					<div class="mt-4 flex items-center gap-2 rounded-lg p-2.5
						{pnoStatus.variant === 'success' ? 'bg-emerald-50 dark:bg-emerald-950/30' : ''}
						{pnoStatus.variant === 'warning' ? 'bg-amber-50 dark:bg-amber-950/30' : ''}
						{pnoStatus.variant === 'error' ? 'bg-rose-50 dark:bg-rose-950/30' : ''}
						{pnoStatus.variant === 'info' ? 'bg-slate-100 dark:bg-slate-800' : ''}
					">
						{#if pnoStatus.valid}
							<CheckCircle class="h-4 w-4 {pnoStatus.variant === 'success' ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}" />
						{:else}
							<AlertTriangle class="h-4 w-4 text-rose-600 dark:text-rose-400" />
						{/if}
						<span class="text-sm font-medium
							{pnoStatus.variant === 'success' ? 'text-emerald-700 dark:text-emerald-300' : ''}
							{pnoStatus.variant === 'warning' ? 'text-amber-700 dark:text-amber-300' : ''}
							{pnoStatus.variant === 'error' ? 'text-rose-700 dark:text-rose-300' : ''}
							{pnoStatus.variant === 'info' ? 'text-slate-600 dark:text-slate-400' : ''}
						">
							{pnoStatus.label}
						</span>
					</div>
				{/if}

				{#if isGerant}
					<div class="mt-4 flex gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
						<button
							class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
							onclick={() => openPnoForm(assurancePno)}
						>
							<Pencil class="h-3.5 w-3.5" />
							Modifier
						</button>
						<button
							class="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700 transition-colors hover:bg-rose-100 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-400"
							onclick={() => handleDeletePno()}
						>
							<Trash2 class="h-3.5 w-3.5" />
							Supprimer
						</button>
					</div>
				{/if}
			</div>
		{:else if !showPnoForm}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
			>
				<Shield class="mb-3 h-10 w-10 text-slate-300 dark:text-slate-600" />
				<p class="text-sm font-medium text-slate-500 dark:text-slate-400">
					Aucune assurance PNO renseignée.
				</p>
				{#if isGerant}
					<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
						Ajoutez votre assurance propriétaire non-occupant pour suivre les échéances.
					</p>
				{/if}
			</div>
		{/if}
	</div>
</div>
