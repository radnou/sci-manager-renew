<script lang="ts">
	import { createChargeForBien, deleteChargeForBien, fetchRegularisation } from '$lib/api';
	import type { RegularisationResult } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { mapChargeTypeLabel } from '$lib/high-value/presentation';
	import { Plus, Trash2, X, Filter, Calculator, CheckCircle, AlertTriangle } from 'lucide-svelte';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { CHARGE_TYPE_OPTIONS } from '$lib/high-value/charges';
	import LockedAction from '$lib/components/LockedAction.svelte';

	interface Props {
		charges: any[];
		isGerant: boolean;
		sciId: string;
		bienId: string | number;
		onRefresh: () => void;
		isDemo?: boolean;
		activeBailId?: string | null;
	}

	let { charges, isGerant, sciId, bienId, onRefresh, isDemo = false, activeBailId = null }: Props = $props();

	// ── Régularisation summary ─────────────────────────
	let regAnnee = $state(new Date().getFullYear() - 1);
	let regLoading = $state(false);
	let regResult = $state<RegularisationResult | null>(null);
	let regExpanded = $state(false);

	async function loadRegularisation() {
		if (!activeBailId) return;
		regLoading = true;
		regResult = null;
		try {
			regResult = await fetchRegularisation(sciId, String(bienId), activeBailId, regAnnee);
		} catch {
			// Silently fail — bail may not exist
		} finally {
			regLoading = false;
		}
	}

	let showChargeComposer = $state(false);
	let chargeSaving = $state(false);
	let type_charge = $state('copropriete');
	let montant = $state(0);
	let date_paiement = $state(new Date().toISOString().slice(0, 10));

	// Charge filters
	let chargeFilterType = $state('tous');
	let chargeFilterYear = $state('tous');

	function resetChargeForm() {
		type_charge = 'copropriete';
		montant = 0;
		date_paiement = new Date().toISOString().slice(0, 10);
	}

	function openChargeComposer() {
		resetChargeForm();
		showChargeComposer = true;
	}

	function closeChargeComposer() {
		showChargeComposer = false;
	}

	async function handleCreateCharge() {
		if (montant < 0) return;
		chargeSaving = true;
		try {
			await createChargeForBien(sciId, bienId, { type_charge, montant, date_paiement });
			addToast({ title: 'Charge ajoutée', variant: 'success' });
			closeChargeComposer();
			onRefresh();
		} catch (err: any) {
			addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
		} finally {
			chargeSaving = false;
		}
	}

	// Filtered charges
	const chargeYears = $derived(() => {
		const years = new Set<string>();
		for (const c of charges) {
			const d = c.date_paiement ?? c.date_charge;
			if (d) years.add(String(d).slice(0, 4));
		}
		return [...years].sort().reverse();
	});

	const filteredCharges = $derived(() => {
		return charges.filter((c) => {
			if (chargeFilterType !== 'tous' && c.type_charge !== chargeFilterType) return false;
			if (chargeFilterYear !== 'tous') {
				const d = c.date_paiement ?? c.date_charge;
				if (!d || !String(d).startsWith(chargeFilterYear)) return false;
			}
			return true;
		});
	});

	const filteredChargeTotal = $derived(() => {
		return filteredCharges().reduce((sum: number, c: any) => sum + Number(c.montant ?? 0), 0);
	});

	// Deferred-delete state
	let pendingDeleteCharge: { id: number; item: any } | null = $state(null);

	function handleDeleteCharge(chargeId: number) {
		const item = charges.find(c => c.id === chargeId);
		if (!item) return;
		pendingDeleteCharge = { id: chargeId, item };
		charges = charges.filter(c => c.id !== chargeId);
		addToast({
			title: 'Charge supprimée',
			variant: 'undo',
			undoCallbacks: {
				onUndo: () => {
					if (pendingDeleteCharge?.id === chargeId) {
						charges = [...charges, pendingDeleteCharge.item].sort((a, b) => (a.id ?? 0) - (b.id ?? 0));
						pendingDeleteCharge = null;
					}
				},
				onExpire: async () => {
					pendingDeleteCharge = null;
					try {
						await deleteChargeForBien(sciId, bienId, chargeId);
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
	<!-- Régularisation annuelle des charges -->
	{#if activeBailId}
		<div class="rounded-2xl border border-amber-200 bg-amber-50/50 p-5 dark:border-amber-900/50 dark:bg-amber-950/20">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2">
					<Calculator class="h-5 w-5 text-amber-600 dark:text-amber-400" />
					<h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Régularisation annuelle des charges</h3>
				</div>
				<button
					onclick={() => { regExpanded = !regExpanded; if (regExpanded && !regResult) loadRegularisation(); }}
					class="text-sm font-medium text-amber-700 transition-colors hover:text-amber-800 dark:text-amber-400 dark:hover:text-amber-300"
				>
					{regExpanded ? 'Masquer' : 'Afficher'}
				</button>
			</div>

			{#if regExpanded}
				<div class="mt-4 space-y-4">
					<div class="flex items-end gap-3">
						<label class="block flex-1">
							<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Année</span>
							<select
								bind:value={regAnnee}
								onchange={() => loadRegularisation()}
								class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
							>
								{#each Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 1 - i) as annee (annee)}
									<option value={annee}>{annee}</option>
								{/each}
							</select>
						</label>
						<button
							onclick={loadRegularisation}
							disabled={regLoading}
							class="inline-flex items-center gap-1.5 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-700 disabled:opacity-50"
						>
							<Calculator class="h-3.5 w-3.5" />
							{regLoading ? 'Calcul...' : 'Calculer'}
						</button>
					</div>

					{#if regResult}
						<div class="grid gap-3 sm:grid-cols-3">
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Provisions collectées</p>
								<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
									{formatEur(regResult.provisions_annuelles)}
								</p>
							</div>
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Charges réelles payées</p>
								<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
									{formatEur(regResult.charges_reelles)}
								</p>
							</div>
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Solde</p>
								<p class="mt-1 text-lg font-bold {regResult.solde > 0 ? 'text-emerald-600 dark:text-emerald-400' : regResult.solde < 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-900 dark:text-slate-100'}">
									{regResult.solde > 0 ? '+' : ''}{formatEur(regResult.solde)}
								</p>
							</div>
						</div>

						{#if regResult.solde > 0}
							<p class="text-sm text-emerald-700 dark:text-emerald-400">
								Trop-perçu : le locataire a payé {formatEur(regResult.solde)} de plus que les charges réelles.
							</p>
						{:else if regResult.solde < 0}
							<p class="text-sm text-rose-700 dark:text-rose-400">
								Complément dû : le locataire doit {formatEur(Math.abs(regResult.solde))} supplémentaires.
							</p>
						{:else}
							<p class="text-sm text-slate-600 dark:text-slate-400">
								Aucun écart — les provisions correspondent aux charges réelles.
							</p>
						{/if}

						{#if regResult.saved?.statut === 'confirme'}
							<div class="flex items-center gap-2 text-sm text-sky-700 dark:text-sky-400">
								<CheckCircle class="h-4 w-4" />
								Confirmée le {formatFrDate(regResult.saved.date_regularisation)}
							</div>
						{:else}
							<div class="flex items-center gap-2 text-sm text-amber-700 dark:text-amber-400">
								<AlertTriangle class="h-4 w-4" />
								Non confirmée — utilisez l'onglet Bail pour confirmer.
							</div>
						{/if}
					{/if}

					<p class="text-xs text-slate-400 dark:text-slate-500">
						Obligation annuelle (loi ALUR art. 23). Le bailleur doit régulariser au moins une fois par an.
					</p>
				</div>
			{/if}
		</div>
	{/if}

	<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="mb-4 flex items-center justify-between">
			<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Charges</h2>
			{#if isGerant}
				<LockedAction {isDemo} action="ajouter une charge">
					<button
						class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
						onclick={showChargeComposer ? closeChargeComposer : openChargeComposer}
					>
						{#if showChargeComposer}
							<X class="h-4 w-4" />
							Fermer
						{:else}
							<Plus class="h-4 w-4" />
							Ajouter une charge
						{/if}
					</button>
				</LockedAction>
			{/if}
		</div>

		{#if isGerant && showChargeComposer}
			<form
				class="mb-5 rounded-2xl border border-sky-200 bg-sky-50/60 p-4 dark:border-sky-900/60 dark:bg-sky-950/20"
				onsubmit={(event) => {
					event.preventDefault();
					handleCreateCharge();
				}}
			>
				<div class="mb-3 flex items-start justify-between gap-3">
					<div>
						<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">Nouvelle charge</p>
						<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
							La saisie reste visible dans l'onglet Charges pour garder le contexte.
						</p>
					</div>
					<button
						type="button"
						class="rounded-full border border-slate-300 p-2 text-slate-500 transition-colors hover:bg-white hover:text-slate-900 dark:border-slate-700 dark:hover:bg-slate-900 dark:hover:text-slate-100"
						onclick={closeChargeComposer}
						aria-label="Fermer le formulaire de charge"
					>
						<X class="h-4 w-4" />
					</button>
				</div>

				<div class="grid gap-4 md:grid-cols-3">
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Type de charge</span>
						<select
							id="charge-type-inline"
							bind:value={type_charge}
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						>
							{#each CHARGE_TYPE_OPTIONS as ct}
								<option value={ct.value}>{ct.label}</option>
							{/each}
						</select>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Montant (€)</span>
						<input
							id="charge-montant-inline"
							type="number"
							bind:value={montant}
							min="0"
							step="0.01"
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Date</span>
						<input
							id="charge-date-inline"
							type="date"
							lang="fr"
							bind:value={date_paiement}
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
				</div>

				<div class="mt-4 flex justify-end gap-2">
					<button
						type="button"
						class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-white dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
						onclick={closeChargeComposer}
					>
						Annuler
					</button>
					<button
						type="submit"
						disabled={chargeSaving}
						class="rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
					>
						{chargeSaving ? 'Ajout…' : 'Ajouter'}
					</button>
				</div>
			</form>
		{/if}

		{#if charges.length > 0}
			<!-- Charge filters -->
			<div class="mb-4 flex flex-wrap items-center gap-3">
				<div class="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
					<Filter class="h-3.5 w-3.5" />
					Filtres
				</div>
				<select
					bind:value={chargeFilterType}
					class="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
					aria-label="Filtrer par type de charge"
				>
					<option value="tous">Tous les types</option>
					{#each CHARGE_TYPE_OPTIONS as ct}
						<option value={ct.value}>{ct.label}</option>
					{/each}
				</select>
				<select
					bind:value={chargeFilterYear}
					class="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
					aria-label="Filtrer par année"
				>
					<option value="tous">Toutes les années</option>
					{#each chargeYears() as year}
						<option value={year}>{year}</option>
					{/each}
				</select>
			</div>
		{/if}

		{#if charges.length === 0}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
			>
				<p class="text-sm text-slate-500 dark:text-slate-400">
					Aucune charge enregistrée pour ce bien.
				</p>
				{#if isGerant}
					<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
						Cliquez sur « Ajouter une charge » pour commencer.
					</p>
				{/if}
			</div>
		{:else if filteredCharges().length === 0}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-8 dark:border-slate-700"
			>
				<p class="text-sm text-slate-500 dark:text-slate-400">
					Aucune charge ne correspond aux filtres sélectionnés.
				</p>
			</div>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-slate-200 dark:border-slate-700">
							<th class="pb-3 pr-4 text-xs font-medium text-slate-500">Libellé</th>
							<th class="pb-3 pr-4 text-xs font-medium text-slate-500">Montant</th>
							<th class="pb-3 pr-4 text-xs font-medium text-slate-500">Date</th>
							{#if isGerant}
								<th class="pb-3 text-xs font-medium text-slate-500">Actions</th>
							{/if}
						</tr>
					</thead>
					<tbody>
						{#each filteredCharges() as charge (charge.id ?? charge.date_paiement)}
							<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
								<td class="py-3 pr-4 font-medium text-slate-900 dark:text-slate-100">
									{mapChargeTypeLabel(charge.type_charge) ?? charge.libelle ?? '—'}
								</td>
								<td class="py-3 pr-4 text-slate-700 dark:text-slate-300">
									{formatEur(charge.montant)}
								</td>
								<td class="py-3 pr-4 text-slate-500 dark:text-slate-400">
									{formatFrDate(charge.date_paiement ?? charge.date_charge)}
								</td>
								{#if isGerant}
									<td class="py-3">
										<button
											class="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-2.5 py-1.5 text-xs font-medium text-rose-700 transition-colors hover:bg-rose-100 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-400"
											title="Supprimer"
											onclick={() => handleDeleteCharge(charge.id)}
										>
											<Trash2 class="h-3 w-3" />
											Supprimer
										</button>
									</td>
								{/if}
							</tr>
						{/each}
					</tbody>
					<tfoot>
						<tr class="border-t border-slate-200 dark:border-slate-700">
							<td class="py-3 pr-4 text-xs font-semibold text-slate-500 dark:text-slate-400">
								{filteredCharges().length} charge{filteredCharges().length > 1 ? 's' : ''}
							</td>
							<td class="py-3 pr-4 font-semibold text-slate-900 dark:text-slate-100">
								{formatEur(filteredChargeTotal())}
							</td>
							<td colspan={isGerant ? 2 : 1}></td>
						</tr>
					</tfoot>
				</table>
			</div>
		{/if}
	</div>
</div>
