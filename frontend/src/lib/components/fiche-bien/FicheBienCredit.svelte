<script lang="ts">
	import type { CreditImmobilierEmbed, AmortissementRow } from '$lib/api';
	import { createCredit, updateCredit, deleteCredit, fetchAmortissement } from '$lib/api';
	import type { CreditCreate, CreditUpdate } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { Landmark, Plus, Trash2, X, Pencil, ChevronDown, ChevronUp, Loader2, Table } from 'lucide-svelte';
	import FieldHint from '$lib/components/FieldHint.svelte';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import {
		announceFicheBienModal,
		subscribeExclusiveFicheBienModal
	} from '$lib/components/fiche-bien/modal-coordinator';

	interface Props {
		credits: CreditImmobilierEmbed[];
		isGerant: boolean;
		sciId: string;
		bienId: string | number;
		onRefresh: () => void;
		isDemo?: boolean;
	}

	let { credits = $bindable(), isGerant, sciId, bienId, onRefresh, isDemo = false }: Props = $props();

	// Form state
	let showForm = $state(false);
	let formLoading = $state(false);
	let editingCredit: CreditImmobilierEmbed | null = $state(null);
	let isEdit = $derived(!!editingCredit);

	// Form fields
	let banque = $state('');
	let numeroContrat = $state('');
	let montantEmprunte = $state(0);
	let tauxNominal = $state(0);
	let tauxAssurance = $state(0);
	let dureeMois = $state(240);
	let dateDebut = $state('');
	let mensualite = $state(0);
	let capitalRestantDu = $state<number | null>(null);
	let typeCredit = $state('amortissable');
	let statut = $state('en_cours');
	let notes = $state('');

	// Amortissement state
	let expandedCreditId: string | number | null = $state(null);
	let amortissementData: AmortissementRow[] = $state([]);
	let amortissementLoading = $state(false);
	let showAllRows = $state(false);

	$effect(() => subscribeExclusiveFicheBienModal('credit', () => { showForm = false; }));

	function resetForm() {
		banque = '';
		numeroContrat = '';
		montantEmprunte = 0;
		tauxNominal = 0;
		tauxAssurance = 0;
		dureeMois = 240;
		dateDebut = '';
		mensualite = 0;
		capitalRestantDu = null;
		typeCredit = 'amortissable';
		statut = 'en_cours';
		notes = '';
		editingCredit = null;
	}

	function openForm(existing: CreditImmobilierEmbed | null = null) {
		if (existing) {
			editingCredit = existing;
			banque = existing.banque;
			numeroContrat = existing.numero_contrat ?? '';
			montantEmprunte = existing.montant_emprunte;
			tauxNominal = existing.taux_nominal;
			tauxAssurance = existing.taux_assurance;
			dureeMois = existing.duree_mois;
			dateDebut = existing.date_debut;
			mensualite = existing.mensualite;
			capitalRestantDu = existing.capital_restant_du;
			typeCredit = existing.type_credit;
			statut = existing.statut;
			notes = '';
		} else {
			resetForm();
		}
		announceFicheBienModal('credit');
		showForm = true;
	}

	function closeForm() {
		showForm = false;
		resetForm();
	}

	async function handleSubmit() {
		if (!banque || !dateDebut || montantEmprunte <= 0 || mensualite <= 0) return;
		formLoading = true;
		try {
			if (isEdit && editingCredit) {
				const data: CreditUpdate = {
					banque,
					numero_contrat: numeroContrat || undefined,
					montant_emprunte: montantEmprunte,
					taux_nominal: tauxNominal,
					taux_assurance: tauxAssurance,
					duree_mois: dureeMois,
					date_debut: dateDebut,
					mensualite,
					capital_restant_du: capitalRestantDu ?? undefined,
					type_credit: typeCredit,
					statut,
					notes: notes || undefined
				};
				await updateCredit(sciId, bienId, editingCredit.id, data);
				addToast({ title: 'Crédit mis à jour', variant: 'success' });
			} else {
				const data: CreditCreate = {
					banque,
					numero_contrat: numeroContrat || undefined,
					montant_emprunte: montantEmprunte,
					taux_nominal: tauxNominal,
					taux_assurance: tauxAssurance,
					duree_mois: dureeMois,
					date_debut: dateDebut,
					mensualite,
					capital_restant_du: capitalRestantDu ?? undefined,
					type_credit: typeCredit,
					statut,
					notes: notes || undefined
				};
				await createCredit(sciId, bienId, data);
				addToast({ title: 'Crédit ajouté', variant: 'success' });
			}
			closeForm();
			onRefresh();
		} catch (err: any) {
			addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
		} finally {
			formLoading = false;
		}
	}

	function handleDelete(creditId: string | number) {
		const item = credits.find(c => c.id === creditId);
		if (!item) return;
		credits = credits.filter(c => c.id !== creditId);
		addToast({
			title: 'Crédit supprimé',
			variant: 'undo',
			undoCallbacks: {
				onUndo: () => {
					credits = [...credits, item];
				},
				onExpire: async () => {
					try {
						await deleteCredit(sciId, bienId, creditId);
						onRefresh();
					} catch (err: any) {
						addToast({ title: err?.message ?? 'Erreur suppression', variant: 'error' });
						onRefresh();
					}
				}
			}
		});
	}

	async function toggleAmortissement(creditId: string | number) {
		if (expandedCreditId === creditId) {
			expandedCreditId = null;
			amortissementData = [];
			showAllRows = false;
			return;
		}
		expandedCreditId = creditId;
		amortissementLoading = true;
		showAllRows = false;
		try {
			amortissementData = await fetchAmortissement(sciId, bienId, creditId);
		} catch (err: any) {
			addToast({ title: err?.message ?? 'Erreur chargement tableau', variant: 'error' });
			amortissementData = [];
		} finally {
			amortissementLoading = false;
		}
	}

	const visibleRows = $derived(showAllRows ? amortissementData : amortissementData.slice(0, 12));

	const typeCreditLabels: Record<string, string> = {
		amortissable: 'Amortissable',
		in_fine: 'In fine',
		relais: 'Relais'
	};

	const statutLabels: Record<string, string> = {
		en_cours: 'En cours',
		rembourse: 'Remboursé',
		restructure: 'Restructuré'
	};

	function formatDuree(mois: number): string {
		const annees = Math.floor(mois / 12);
		const resteM = mois % 12;
		if (annees === 0) return `${resteM} mois`;
		if (resteM === 0) return `${annees} an${annees > 1 ? 's' : ''}`;
		return `${annees} an${annees > 1 ? 's' : ''} et ${resteM} mois`;
	}
</script>

<div class="space-y-6">
	<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="mb-4 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<Landmark class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Crédit immobilier</h2>
			</div>
			{#if isGerant && !showForm}
				<button
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
					onclick={() => openForm()}
					disabled={isDemo}
				>
					<Plus class="h-4 w-4" />
					Ajouter
				</button>
			{/if}
		</div>

		{#if showForm}
			<form
				class="mb-5 rounded-2xl border border-sky-200 bg-sky-50/60 p-4 dark:border-sky-900/60 dark:bg-sky-950/20"
				onsubmit={(event) => { event.preventDefault(); handleSubmit(); }}
			>
				<div class="mb-3 flex items-start justify-between gap-3">
					<div>
						<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
							{isEdit ? 'Modifier le crédit' : 'Ajouter un crédit immobilier'}
						</p>
						<p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
							Les intérêts d'emprunt sont déductibles (CERFA 2044, ligne 250).
						</p>
					</div>
					<button
						type="button"
						class="rounded-full border border-slate-300 p-2 text-slate-500 transition-colors hover:bg-white hover:text-slate-900 dark:border-slate-700 dark:hover:bg-slate-900 dark:hover:text-slate-100"
						onclick={closeForm}
						aria-label="Fermer le formulaire"
					>
						<X class="h-4 w-4" />
					</button>
				</div>

				<div class="grid gap-4 md:grid-cols-2">
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Banque</span>
						<input
							type="text"
							bind:value={banque}
							required
							placeholder="Ex : Crédit Agricole, BNP..."
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">N° contrat</span>
						<input
							type="text"
							bind:value={numeroContrat}
							placeholder="Optionnel"
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Montant emprunté (€)</span>
						<input
							type="number"
							bind:value={montantEmprunte}
							min="1"
							step="0.01"
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Mensualité (€)</span>
						<input
							type="number"
							bind:value={mensualite}
							min="1"
							step="0.01"
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Taux nominal (%)<FieldHint text="Taux d'interet hors assurance (different du TAEG). Visible sur votre offre de pret." /></span>
						<input
							type="number"
							bind:value={tauxNominal}
							min="0"
							step="0.001"
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Taux assurance (%)<FieldHint text="Taux annuel de l'assurance emprunteur. Souvent entre 0.1% et 0.5% selon l'age et le profil." /></span>
						<input
							type="number"
							bind:value={tauxAssurance}
							min="0"
							step="0.001"
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Durée (mois)</span>
						<input
							type="number"
							bind:value={dureeMois}
							min="1"
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Date de début</span>
						<input
							type="date"
							lang="fr"
							bind:value={dateDebut}
							required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Capital restant dû (€)<FieldHint text="Optionnel. Si renseigne, utilise cette valeur au lieu du calcul automatique depuis le tableau d'amortissement." /></span>
						<input
							type="number"
							bind:value={capitalRestantDu}
							min="0"
							step="0.01"
							placeholder="Optionnel"
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</label>
					<label class="block">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Type de crédit<FieldHint text="Amortissable : mensualites capital+interets. In fine : interets seuls, capital rembourse a terme. Relais : pret court terme en attente de vente." /></span>
						<select
							bind:value={typeCredit}
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						>
							<option value="amortissable">Amortissable</option>
							<option value="in_fine">In fine</option>
							<option value="relais">Relais</option>
						</select>
					</label>
					{#if isEdit}
						<label class="block">
							<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Statut</span>
							<select
								bind:value={statut}
								class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
							>
								<option value="en_cours">En cours</option>
								<option value="rembourse">Remboursé</option>
								<option value="restructure">Restructuré</option>
							</select>
						</label>
					{/if}
					<label class="block md:col-span-2">
						<span class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Notes</span>
						<textarea
							bind:value={notes}
							rows="2"
							placeholder="Notes optionnelles..."
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						></textarea>
					</label>
				</div>

				<div class="mt-4 flex justify-end gap-2">
					<button
						type="button"
						class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-white dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
						onclick={closeForm}
					>
						Annuler
					</button>
					<button
						type="submit"
						disabled={formLoading}
						class="rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
					>
						{formLoading ? 'Enregistrement...' : isEdit ? 'Mettre à jour' : 'Ajouter'}
					</button>
				</div>
			</form>
		{/if}

		{#if credits.length === 0 && !showForm}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
			>
				<Landmark class="mb-3 h-10 w-10 text-slate-300 dark:text-slate-600" />
				<p class="text-sm font-medium text-slate-500 dark:text-slate-400">
					Aucun crédit immobilier renseigné.
				</p>
				{#if isGerant}
					<p class="mt-1 max-w-sm text-center text-xs text-slate-400 dark:text-slate-500">
						Ajoutez vos emprunts pour suivre le capital restant dû et générer le tableau d'amortissement.
					</p>
				{/if}
			</div>
		{:else}
			<div class="space-y-4">
				{#each credits as credit (credit.id)}
					<div class="rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-5 dark:border-slate-700 dark:from-slate-900 dark:to-slate-950">
						<div class="flex items-start justify-between gap-4">
							<div class="flex items-start gap-4">
								<div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-sky-100 dark:bg-sky-900/40">
									<Landmark class="h-6 w-6 text-sky-600 dark:text-sky-400" />
								</div>
								<div>
									<p class="text-base font-semibold text-slate-900 dark:text-slate-100">
										{credit.banque}
									</p>
									{#if credit.numero_contrat}
										<p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
											Contrat n° {credit.numero_contrat}
										</p>
									{/if}
								</div>
							</div>
							<span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium
								{credit.statut === 'en_cours' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400' : ''}
								{credit.statut === 'rembourse' ? 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400' : ''}
								{credit.statut === 'restructure' ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400' : ''}
							">
								{statutLabels[credit.statut] ?? credit.statut}
							</span>
						</div>

						<div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Montant emprunté</p>
								<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{formatEur(credit.montant_emprunte)}</p>
							</div>
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Taux</p>
								<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{credit.taux_nominal}%</p>
								{#if credit.taux_assurance > 0}
									<p class="text-xs text-slate-400 dark:text-slate-500">+ {credit.taux_assurance}% assurance</p>
								{/if}
							</div>
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Mensualité</p>
								<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{formatEur(credit.mensualite)}</p>
							</div>
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Durée</p>
								<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{formatDuree(credit.duree_mois)}</p>
							</div>
						</div>

						<div class="mt-3 grid gap-3 sm:grid-cols-3">
							<div>
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Capital restant dû</p>
								<p class="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">
									{credit.capital_restant_du != null ? formatEur(credit.capital_restant_du) : '—'}
								</p>
							</div>
							<div>
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Type</p>
								<p class="mt-1 text-sm text-slate-700 dark:text-slate-300">
									{typeCreditLabels[credit.type_credit] ?? credit.type_credit}
								</p>
							</div>
							<div>
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Date de début</p>
								<p class="mt-1 text-sm text-slate-700 dark:text-slate-300">
									{formatFrDate(credit.date_debut)}
								</p>
							</div>
						</div>

						<div class="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
							<button
								class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
								onclick={() => toggleAmortissement(credit.id)}
							>
								<Table class="h-3.5 w-3.5" />
								{expandedCreditId === credit.id ? 'Masquer' : 'Tableau d\'amortissement'}
							</button>
							{#if isGerant}
								<button
									class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
									onclick={() => openForm(credit)}
									disabled={isDemo}
								>
									<Pencil class="h-3.5 w-3.5" />
									Modifier
								</button>
								<button
									class="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700 transition-colors hover:bg-rose-100 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-400"
									onclick={() => handleDelete(credit.id)}
									disabled={isDemo}
								>
									<Trash2 class="h-3.5 w-3.5" />
									Supprimer
								</button>
							{/if}
						</div>

						{#if expandedCreditId === credit.id}
							<div class="mt-4">
								{#if amortissementLoading}
									<div class="flex items-center justify-center py-8">
										<Loader2 class="h-6 w-6 animate-spin text-sky-600" />
									</div>
								{:else if amortissementData.length > 0}
									<div class="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
										<table class="w-full text-left text-sm">
											<thead>
												<tr class="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-900">
													<th class="px-3 py-2.5 text-xs font-medium text-slate-500">Mois</th>
													<th class="px-3 py-2.5 text-xs font-medium text-slate-500">Date</th>
													<th class="px-3 py-2.5 text-right text-xs font-medium text-slate-500">Mensualité</th>
													<th class="px-3 py-2.5 text-right text-xs font-medium text-slate-500">Capital</th>
													<th class="px-3 py-2.5 text-right text-xs font-medium text-slate-500">Intérêts</th>
													{#if credit.taux_assurance > 0}
														<th class="px-3 py-2.5 text-right text-xs font-medium text-slate-500">Assurance</th>
													{/if}
													<th class="px-3 py-2.5 text-right text-xs font-medium text-slate-500">CRD</th>
												</tr>
											</thead>
											<tbody>
												{#each visibleRows as row (row.mois)}
													<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
														<td class="px-3 py-2 text-slate-700 dark:text-slate-300">{row.mois}</td>
														<td class="px-3 py-2 text-slate-500 dark:text-slate-400">{formatFrDate(row.date)}</td>
														<td class="px-3 py-2 text-right font-medium text-slate-900 dark:text-slate-100">{formatEur(row.mensualite)}</td>
														<td class="px-3 py-2 text-right text-slate-700 dark:text-slate-300">{formatEur(row.capital)}</td>
														<td class="px-3 py-2 text-right text-slate-500 dark:text-slate-400">{formatEur(row.interets)}</td>
														{#if credit.taux_assurance > 0}
															<td class="px-3 py-2 text-right text-slate-500 dark:text-slate-400">{formatEur(row.assurance)}</td>
														{/if}
														<td class="px-3 py-2 text-right font-medium text-slate-900 dark:text-slate-100">{formatEur(row.capital_restant)}</td>
													</tr>
												{/each}
											</tbody>
										</table>
									</div>
									{#if amortissementData.length > 12}
										<div class="mt-3 flex justify-center">
											<button
												class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
												onclick={() => showAllRows = !showAllRows}
											>
												{#if showAllRows}
													<ChevronUp class="h-4 w-4" />
													Réduire ({amortissementData.length} lignes)
												{:else}
													<ChevronDown class="h-4 w-4" />
													Voir les {amortissementData.length} échéances
												{/if}
											</button>
										</div>
									{/if}
								{:else}
									<p class="py-4 text-center text-sm text-slate-500 dark:text-slate-400">
										Aucune donnée d'amortissement disponible.
									</p>
								{/if}
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
