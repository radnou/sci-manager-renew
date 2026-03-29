<script lang="ts">
	import type { BailEmbed, LoyerEmbed, CongeType, RegularisationResult, AvenantBailPayload } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { updateLocataire, cloturerBail, donnerConge, fetchRegularisation, confirmRegularisation, creerAvenant, updateBail, type ClotureBailPayload } from '$lib/api';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { Plus, Pencil, Users, Calendar, History, Mail, Phone, CheckCircle, X, Save, Lock, AlertTriangle, RefreshCw, Calculator, FileSignature, Loader2, ClipboardCheck, Upload, FileText } from 'lucide-svelte';
	import BailModal from '$lib/components/fiche-bien/modals/BailModal.svelte';
	import {
		announceFicheBienModal,
		subscribeExclusiveFicheBienModal
	} from '$lib/components/fiche-bien/modal-coordinator';

	interface Props {
		bail: BailEmbed | null;
		loyers?: LoyerEmbed[];
		isGerant: boolean;
		sciId: string;
		bienId: string | number;
		onRefresh: () => void;
	}

	let { bail, loyers = [], isGerant, sciId, bienId, onRefresh }: Props = $props();

	let showBailModal = $state(false);
	let editBail: BailEmbed | null = $state(null);

	$effect(() => {
		return subscribeExclusiveFicheBienModal('bail', () => {
			showBailModal = false;
		});
	});

	function openBailModal(item: BailEmbed | null = null) {
		editBail = item;
		announceFicheBienModal('bail');
		showBailModal = true;
	}

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

	const loyerStatutConfig: Record<string, { label: string; class: string }> = {
		paye: {
			label: 'Payé',
			class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
		},
		en_attente: {
			label: 'En attente',
			class: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
		},
		en_retard: {
			label: 'En retard',
			class: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
		}
	};

	function getLoyerStatut(statut: string) {
		return loyerStatutConfig[statut] ?? { label: statut, class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' };
	}

	// Compute loyer summary from available data
	const loyerSummary = $derived(() => {
		if (!loyers || loyers.length === 0) return null;
		const total = loyers.length;
		const payes = loyers.filter(l => l.statut === 'paye').length;
		const totalPaye = loyers.filter(l => l.statut === 'paye').reduce((sum, l) => sum + Number(l.montant ?? 0), 0);
		const totalDu = loyers.reduce((sum, l) => sum + Number(l.montant ?? 0), 0);
		const solde = totalDu - totalPaye;
		// Last 3 loyers sorted by date desc
		const sorted = [...loyers].sort((a, b) => b.date_loyer.localeCompare(a.date_loyer));
		const last3 = sorted.slice(0, 3);
		return { total, payes, totalPaye, totalDu, solde, last3 };
	});

	// ── Édition locataire ─────────────────────────
	let editingLocataireId = $state<string | number | null>(null);
	let editLocNom = $state('');
	let editLocEmail = $state('');
	let editLocTelephone = $state('');
	let savingLocataire = $state(false);

	function startEditLocataire(loc: any) {
		editingLocataireId = loc.id;
		editLocNom = loc.nom || '';
		editLocEmail = loc.email || '';
		editLocTelephone = loc.telephone || '';
	}

	function cancelEditLocataire() {
		editingLocataireId = null;
	}

	async function saveLocataire() {
		if (!editingLocataireId) return;
		savingLocataire = true;
		try {
			await updateLocataire(editingLocataireId, {
				nom: editLocNom,
				email: editLocEmail || undefined,
				telephone: editLocTelephone || undefined,
			});
			addToast({ title: 'Locataire mis à jour', variant: 'success' });
			editingLocataireId = null;
			onRefresh();
		} catch {
			addToast({ title: 'Erreur lors de la mise à jour', variant: 'error' });
		} finally {
			savingLocataire = false;
		}
	}

	// ── Clôture bail ─────────────────────────
	let showClotureForm = $state(false);
	let clotureSaving = $state(false);
	let clotureFinEffective = $state('');
	let clotureEtatLieux = $state('');
	let clotureDepotRestitue = $state(0);
	let clotureRetenues = $state('');
	let clotureMotif = $state<ClotureBailPayload['motif']>('conge_locataire');

	// ── Congé bail ─────────────────────────
	let showCongeForm = $state(false);
	let congeSaving = $state(false);
	let congeType = $state<CongeType>('locataire');
	let congeDateNotification = $state('');
	let congeMotif = $state('');

	const congeTypeOptions: Array<{ value: CongeType; label: string; preavis: number }> = [
		{ value: 'locataire', label: 'Congé du locataire', preavis: 3 },
		{ value: 'bailleur', label: 'Congé du bailleur', preavis: 6 }
	];

	const congeDateEffet = $derived(() => {
		if (!congeDateNotification) return null;
		const preavisMois = congeType === 'bailleur' ? 6 : 3;
		const d = new Date(congeDateNotification);
		d.setMonth(d.getMonth() + preavisMois);
		return d.toISOString().split('T')[0];
	});

	function openCongeForm() {
		congeDateNotification = new Date().toISOString().split('T')[0];
		congeType = 'locataire';
		congeMotif = '';
		showCongeForm = true;
	}

	function cancelConge() {
		showCongeForm = false;
	}

	async function submitConge() {
		if (!bail) return;
		const dateEffet = congeDateEffet();
		if (!congeDateNotification || !dateEffet) return;
		congeSaving = true;
		try {
			await donnerConge(sciId, String(bienId), String(bail.id), {
				type_conge: congeType,
				date_notification: congeDateNotification,
				motif: congeMotif || undefined,
				date_effet: dateEffet
			});
			addToast({ title: 'Congé enregistré', variant: 'success' });
			showCongeForm = false;
			onRefresh();
		} catch {
			addToast({ title: 'Erreur lors de l\'enregistrement du congé', variant: 'error' });
		} finally {
			congeSaving = false;
		}
	}

	// ── Reconduction tacite ─────────────────────────
	const isReconduitTacitement = $derived(() => {
		if (!bail || bail.statut !== 'en_cours' || !bail.date_fin) return false;
		return new Date(bail.date_fin) < new Date();
	});

	const prochaineEcheanceReconduction = $derived(() => {
		if (!bail?.date_fin) return null;
		const d = new Date(bail.date_fin);
		d.setFullYear(d.getFullYear() + 3);
		return d.toISOString().split('T')[0];
	});

	// ── Régularisation charges ─────────────────────────
	let showRegularisation = $state(false);
	let regularisationAnnee = $state(new Date().getFullYear() - 1);
	let regularisationLoading = $state(false);
	let regularisationResult = $state<RegularisationResult | null>(null);
	let regularisationConfirming = $state(false);
	let regularisationNotes = $state('');

	async function handleRegularisation() {
		if (!bail) return;
		regularisationLoading = true;
		regularisationResult = null;
		try {
			regularisationResult = await fetchRegularisation(
				sciId,
				String(bienId),
				String(bail.id),
				regularisationAnnee
			);
		} catch {
			addToast({ title: 'Erreur lors du calcul de la régularisation', variant: 'error' });
		} finally {
			regularisationLoading = false;
		}
	}

	async function handleConfirmRegularisation() {
		if (!bail || !regularisationResult) return;
		regularisationConfirming = true;
		try {
			await confirmRegularisation(
				sciId,
				String(bienId),
				String(bail.id),
				regularisationAnnee,
				regularisationNotes || undefined
			);
			addToast({ title: 'Régularisation confirmée', variant: 'success' });
			// Refresh to show saved status
			await handleRegularisation();
			regularisationNotes = '';
		} catch {
			addToast({ title: 'Erreur lors de la confirmation', variant: 'error' });
		} finally {
			regularisationConfirming = false;
		}
	}

	const motifOptions: Array<{ value: ClotureBailPayload['motif']; label: string }> = [
		{ value: 'conge_locataire', label: 'Conge locataire' },
		{ value: 'conge_bailleur', label: 'Conge bailleur' },
		{ value: 'resiliation_amiable', label: 'Resiliation amiable' },
		{ value: 'resiliation_judiciaire', label: 'Resiliation judiciaire' }
	];

	function openClotureForm() {
		clotureFinEffective = new Date().toISOString().split('T')[0];
		clotureEtatLieux = new Date().toISOString().split('T')[0];
		clotureDepotRestitue = bail?.depot_garantie ?? 0;
		clotureRetenues = '';
		clotureMotif = 'conge_locataire';
		showClotureForm = true;
	}

	function cancelCloture() {
		showClotureForm = false;
	}

	async function submitCloture() {
		if (!bail) return;
		clotureSaving = true;
		try {
			await cloturerBail(sciId, String(bienId), String(bail.id), {
				date_fin_effective: clotureFinEffective,
				date_etat_lieux_sortie: clotureEtatLieux,
				montant_depot_restitue: clotureDepotRestitue,
				detail_retenues: clotureRetenues || undefined,
				motif: clotureMotif
			});
			addToast({ title: 'Bail cloture avec succes', variant: 'success' });
			showClotureForm = false;
			onRefresh();
		} catch {
			addToast({ title: 'Erreur lors de la cloture du bail', variant: 'error' });
		} finally {
			clotureSaving = false;
		}
	}

	// ── Avenant bail ─────────────────────────
	let showAvenantForm = $state(false);
	let avenantSaving = $state(false);
	let avenantType = $state<AvenantBailPayload['type_avenant']>('revision_loyer');
	let avenantNouvelleValeur = $state('');
	let avenantDateEffet = $state('');
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

	function openAvenantForm() {
		avenantType = 'revision_loyer';
		avenantNouvelleValeur = '';
		avenantDateEffet = new Date().toISOString().split('T')[0];
		avenantMotif = '';
		showAvenantForm = true;
	}

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
			showAvenantForm = false;
			onRefresh();
		} catch {
			addToast({ title: 'Erreur', description: 'Impossible de créer l\'avenant.', variant: 'error' });
		} finally {
			avenantSaving = false;
		}
	}

	// ── État des lieux d'entrée ─────────────────────────
	let showEdlForm = $state(false);
	let edlSaving = $state(false);
	let edlDate = $state('');
	let edlNotes = $state('');

	function openEdlForm() {
		edlDate = bail?.etat_lieux_entree ?? new Date().toISOString().split('T')[0];
		edlNotes = bail?.etat_lieux_entree_notes ?? '';
		showEdlForm = true;
	}

	async function saveEdl() {
		if (!bail || !edlDate) return;
		edlSaving = true;
		try {
			await updateBail(sciId, String(bienId), String(bail.id), {
				etat_lieux_entree: edlDate,
				etat_lieux_entree_notes: edlNotes || undefined
			});
			addToast({ title: 'État des lieux enregistré', variant: 'success' });
			showEdlForm = false;
			onRefresh();
		} catch {
			addToast({ title: 'Erreur', description: 'Impossible d\'enregistrer l\'état des lieux.', variant: 'error' });
		} finally {
			edlSaving = false;
		}
	}
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Bail</h2>
		<div class="flex items-center gap-2">
			<a
				href={`/scis/${sciId}/biens/${bienId}/baux`}
				class="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 transition-colors hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
			>
				<History class="h-4 w-4" />
				Historique
			</a>
			{#if isGerant && (!bail || bail.statut === 'expire' || bail.statut === 'resilie')}
				<button
					onclick={() => openBailModal()}
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
			<Users class="mb-3 h-10 w-10 text-slate-400 dark:text-slate-500" />
			<p class="text-sm font-medium text-slate-500 dark:text-slate-400">Aucun bail actif pour ce bien.</p>
			{#if isGerant}
				<p class="mt-1.5 text-sm text-slate-400 dark:text-slate-500">
					Cliquez sur "Créer un bail" pour commencer.
				</p>
			{/if}
		</div>
	{:else}
		{@const statut = getStatut(bail.statut)}
		<div class="space-y-5">
			<!-- Statut badge + modify button -->
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2">
					<span
						class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium {statut.class}"
					>
						{statut.label}
					</span>
					{#if isReconduitTacitement()}
						<span class="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
							<RefreshCw class="h-3 w-3" />
							Reconduit tacitement
						</span>
					{/if}
				</div>
				{#if isGerant}
					<div class="flex items-center gap-2">
						{#if bail.statut === 'en_cours'}
							<button
								onclick={openCongeForm}
								class="inline-flex items-center gap-1.5 text-sm font-medium text-amber-600 transition-colors hover:text-amber-700 dark:text-amber-400 dark:hover:text-amber-300"
							>
								<AlertTriangle class="h-3.5 w-3.5" />
								Donner congé
							</button>
							<button
								onclick={openClotureForm}
								class="inline-flex items-center gap-1.5 text-sm font-medium text-rose-600 transition-colors hover:text-rose-700 dark:text-rose-400 dark:hover:text-rose-300"
							>
								<Lock class="h-3.5 w-3.5" />
								Cloturer le bail
							</button>
						{/if}
						<button
							onclick={openAvenantForm}
							class="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 transition-colors hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
						>
							<FileSignature class="h-3.5 w-3.5" />
							Créer un avenant
						</button>
						<button
							onclick={() => openBailModal(bail)}
							class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
						>
							<Pencil class="h-3.5 w-3.5" />
							Modifier
						</button>
					</div>
				{/if}
			</div>

			<!-- Reconduction tacite info -->
			{#if isReconduitTacitement()}
				<div class="rounded-xl border border-amber-200 bg-amber-50/50 p-4 dark:border-amber-800/50 dark:bg-amber-900/10">
					<div class="flex items-start gap-3">
						<RefreshCw class="mt-0.5 h-4 w-4 text-amber-600 dark:text-amber-400" />
						<div>
							<p class="text-sm font-medium text-amber-800 dark:text-amber-200">
								Ce bail a été reconduit tacitement.
							</p>
							{#if prochaineEcheanceReconduction()}
								<p class="mt-1 text-sm text-amber-700 dark:text-amber-300">
									Prochaine échéance estimée : {formatFrDate(prochaineEcheanceReconduction()!)}
								</p>
							{/if}
						</div>
					</div>
				</div>
			{/if}

			<!-- Cloture form -->
			{#if showClotureForm}
				<div class="rounded-xl border border-rose-200 bg-rose-50/50 p-5 dark:border-rose-800/50 dark:bg-rose-900/10">
					<h3 class="mb-4 text-sm font-semibold text-slate-900 dark:text-slate-100">Cloturer le bail</h3>
					<div class="grid gap-4 sm:grid-cols-2">
						<label class="block">
							<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Date de fin effective</span>
							<input
								type="date"
								bind:value={clotureFinEffective}
								class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
							/>
						</label>
						<label class="block">
							<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Date etat des lieux de sortie</span>
							<input
								type="date"
								bind:value={clotureEtatLieux}
								class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
							/>
						</label>
						<label class="block">
							<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Montant depot restitue</span>
							<input
								type="number"
								step="0.01"
								min="0"
								bind:value={clotureDepotRestitue}
								class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
							/>
						</label>
						<label class="block">
							<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Motif</span>
							<select
								bind:value={clotureMotif}
								class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
							>
								{#each motifOptions as opt (opt.value)}
									<option value={opt.value}>{opt.label}</option>
								{/each}
							</select>
						</label>
					</div>
					<label class="mt-4 block">
						<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Detail retenues (optionnel)</span>
						<textarea
							bind:value={clotureRetenues}
							rows="2"
							placeholder="Ex: Reparation mur salon, nettoyage..."
							class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
						></textarea>
					</label>
					<div class="mt-4 flex justify-end gap-2">
						<button
							onclick={cancelCloture}
							class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
						>
							Annuler
						</button>
						<button
							onclick={submitCloture}
							disabled={clotureSaving || !clotureFinEffective || !clotureEtatLieux}
							class="inline-flex items-center gap-1.5 rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50"
						>
							<Lock class="h-3.5 w-3.5" />
							{clotureSaving ? 'Cloture en cours...' : 'Cloturer le bail'}
						</button>
					</div>
				</div>
			{/if}

			<!-- Congé form -->
			{#if showCongeForm}
				<div class="rounded-xl border border-amber-200 bg-amber-50/50 p-5 dark:border-amber-800/50 dark:bg-amber-900/10">
					<h3 class="mb-4 text-sm font-semibold text-slate-900 dark:text-slate-100">Donner congé</h3>
					<div class="grid gap-4 sm:grid-cols-2">
						<label class="block">
							<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Type de congé</span>
							<select
								bind:value={congeType}
								class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
							>
								{#each congeTypeOptions as opt (opt.value)}
									<option value={opt.value}>{opt.label} ({opt.preavis} mois de préavis)</option>
								{/each}
							</select>
						</label>
						<label class="block">
							<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Date de notification</span>
							<input
								type="date"
								bind:value={congeDateNotification}
								class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
							/>
						</label>
					</div>
					<label class="mt-4 block">
						<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Motif (optionnel)</span>
						<textarea
							bind:value={congeMotif}
							rows="2"
							placeholder="Ex: Vente du bien, reprise pour habiter..."
							class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
						></textarea>
					</label>
					{#if congeDateEffet()}
						<div class="mt-4 rounded-lg border border-sky-200 bg-sky-50 p-3 dark:border-sky-800 dark:bg-sky-950/30">
							<p class="text-sm font-medium text-sky-800 dark:text-sky-200">
								Le bail prendra fin le {formatFrDate(congeDateEffet()!)}
							</p>
							<p class="mt-1 text-xs text-sky-600 dark:text-sky-400">
								Préavis de {congeType === 'bailleur' ? '6' : '3'} mois à compter de la notification.
							</p>
						</div>
					{/if}
					<div class="mt-4 flex justify-end gap-2">
						<button
							onclick={cancelConge}
							class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
						>
							Annuler
						</button>
						<button
							onclick={submitConge}
							disabled={congeSaving || !congeDateNotification}
							class="inline-flex items-center gap-1.5 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
						>
							<AlertTriangle class="h-3.5 w-3.5" />
							{congeSaving ? 'Envoi en cours...' : 'Donner congé'}
						</button>
					</div>
				</div>
			{/if}

			<!-- Avenant au bail -->
			{#if showAvenantForm}
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
						<button onclick={() => { showAvenantForm = false; }} class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800">
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

			<!-- Régularisation des charges -->
			{#if bail.statut === 'en_cours'}
				<div>
					<div class="flex items-center justify-between">
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
							Régularisation des charges
						</p>
						{#if isGerant}
							<button
								onclick={() => { showRegularisation = !showRegularisation; }}
								class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
							>
								<Calculator class="h-3.5 w-3.5" />
								{showRegularisation ? 'Masquer' : 'Régulariser'}
							</button>
						{/if}
					</div>

					{#if showRegularisation}
						<div class="mt-3 rounded-xl border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-700 dark:bg-slate-900/50">
							<div class="flex items-end gap-3">
								<label class="block flex-1">
									<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Année</span>
									<select
										bind:value={regularisationAnnee}
										class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
									>
										{#each Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 1 - i) as annee (annee)}
											<option value={annee}>{annee}</option>
										{/each}
									</select>
								</label>
								<button
									onclick={handleRegularisation}
									disabled={regularisationLoading}
									class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
								>
									<Calculator class="h-3.5 w-3.5" />
									{regularisationLoading ? 'Calcul...' : 'Calculer la régularisation'}
								</button>
							</div>

							{#if regularisationResult}
								<div class="mt-4 space-y-3">
									<div class="grid gap-3 sm:grid-cols-3">
										<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
											<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Provisions annuelles</p>
											<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{formatEur(regularisationResult.provisions_annuelles)}</p>
										</div>
										<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
											<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Charges réelles</p>
											<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{formatEur(regularisationResult.charges_reelles)}</p>
										</div>
										<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
											<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Solde</p>
											<p class="mt-1 text-lg font-bold {regularisationResult.solde > 0 ? 'text-emerald-600 dark:text-emerald-400' : regularisationResult.solde < 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-900 dark:text-slate-100'}">
												{formatEur(Math.abs(regularisationResult.solde))}
											</p>
										</div>
									</div>
									{#if regularisationResult.solde > 0}
										<div class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-800 dark:bg-emerald-950/30">
											<p class="text-sm font-medium text-emerald-800 dark:text-emerald-200">
												Le locataire a trop payé de {formatEur(regularisationResult.solde)}
											</p>
											<p class="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
												Un remboursement est dû au locataire.
											</p>
										</div>
									{:else if regularisationResult.solde < 0}
										<div class="rounded-lg border border-rose-200 bg-rose-50 p-3 dark:border-rose-800 dark:bg-rose-950/30">
											<p class="text-sm font-medium text-rose-800 dark:text-rose-200">
												Le locataire doit un complément de {formatEur(Math.abs(regularisationResult.solde))}
											</p>
											<p class="mt-1 text-xs text-rose-600 dark:text-rose-400">
												Un appel de régularisation peut être émis.
											</p>
										</div>
									{:else}
										<div class="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
											<p class="text-sm font-medium text-slate-700 dark:text-slate-300">
												Aucun écart — les provisions correspondent aux charges réelles.
											</p>
										</div>
									{/if}
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/if}

			<!-- Locataires Cards -->
			<div>
				<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
					{bail.locataires.length > 1 ? 'Locataires (colocation)' : 'Locataire'}
				</p>
				{#if bail.locataires.length === 0}
					<div class="mt-2 rounded-xl border border-dashed border-slate-300 p-4 text-center dark:border-slate-700">
						<Users class="mx-auto mb-2 h-8 w-8 text-slate-300 dark:text-slate-600" />
						<p class="text-sm text-slate-400 dark:text-slate-500">Aucun locataire rattaché</p>
					</div>
				{:else}
					<div class="mt-3 space-y-3">
						{#each bail.locataires as loc (loc.id)}
							<div class="rounded-xl border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-700 dark:bg-slate-900/50">
								{#if editingLocataireId === loc.id}
									<!-- Formulaire édition inline -->
									<div class="space-y-3">
										<div class="flex items-center justify-between">
											<p class="text-sm font-semibold text-slate-700 dark:text-slate-300">Modifier le locataire</p>
											<button onclick={cancelEditLocataire} class="rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
												<X class="h-4 w-4" />
											</button>
										</div>
										<div class="grid gap-3 sm:grid-cols-3">
											<label class="block">
												<span class="text-xs font-medium text-slate-500 dark:text-slate-400">Nom</span>
												<input type="text" bind:value={editLocNom} class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
											</label>
											<label class="block">
												<span class="text-xs font-medium text-slate-500 dark:text-slate-400">Email</span>
												<input type="email" bind:value={editLocEmail} class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
											</label>
											<label class="block">
												<span class="text-xs font-medium text-slate-500 dark:text-slate-400">Téléphone</span>
												<input type="tel" bind:value={editLocTelephone} class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800" />
											</label>
										</div>
										<div class="flex justify-end gap-2">
											<button onclick={cancelEditLocataire} class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800">Annuler</button>
											<button onclick={saveLocataire} disabled={savingLocataire || !editLocNom.trim()} class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50">
												<Save class="h-3.5 w-3.5" />
												{savingLocataire ? 'Enregistrement...' : 'Enregistrer'}
											</button>
										</div>
									</div>
								{:else}
									<!-- Carte locataire lecture -->
									<div class="flex items-start justify-between gap-3">
										<div class="min-w-0 flex-1">
											<div class="flex items-center gap-2.5">
												<p class="text-base font-semibold text-slate-900 dark:text-slate-100">
													{loc.prenom ? `${loc.prenom} ${loc.nom}` : loc.nom}
												</p>
												<span class="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
													<CheckCircle class="h-3 w-3" />
													Locataire actif
												</span>
											</div>
											<div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1">
												{#if loc.email}
													<a href="mailto:{loc.email}" class="inline-flex items-center gap-1.5 text-sm text-sky-600 hover:text-sky-700 dark:text-sky-400">
														<Mail class="h-3.5 w-3.5" />
														{loc.email}
													</a>
												{/if}
												{#if loc.telephone}
													<a href="tel:{loc.telephone}" class="inline-flex items-center gap-1.5 text-sm text-sky-600 hover:text-sky-700 dark:text-sky-400">
														<Phone class="h-3.5 w-3.5" />
														{loc.telephone}
													</a>
												{/if}
											</div>
										</div>
										<div class="flex shrink-0 items-center gap-1.5">
											{#if isGerant}
												<button
													onclick={() => startEditLocataire(loc)}
													class="rounded-lg border border-slate-200 bg-white p-2 text-slate-500 transition-colors hover:border-sky-300 hover:text-sky-600 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-sky-700 dark:hover:text-sky-400"
													title="Modifier le locataire"
												>
													<Pencil class="h-4 w-4" />
												</button>
											{/if}
											{#if loc.email}
												<a href="mailto:{loc.email}" class="rounded-lg border border-slate-200 bg-white p-2 text-slate-500 hover:border-sky-300 hover:text-sky-600 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-sky-700 dark:hover:text-sky-400" title="Email">
													<Mail class="h-4 w-4" />
												</a>
											{/if}
											{#if loc.telephone}
												<a href="tel:{loc.telephone}" class="rounded-lg border border-slate-200 bg-white p-2 text-slate-500 hover:border-sky-300 hover:text-sky-600 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-sky-700 dark:hover:text-sky-400" title="Appeler">
													<Phone class="h-4 w-4" />
												</a>
											{/if}
										</div>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Historique des loyers (summary) -->
			{#if loyerSummary()}
				{@const summary = loyerSummary()!}
				<div>
					<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
						Historique des loyers
					</p>
					<div class="mt-2 rounded-xl border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-700 dark:bg-slate-900/50">
						<div class="grid gap-3 sm:grid-cols-3">
							<div class="text-center">
								<p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
									{summary.payes}<span class="text-sm font-normal text-slate-400">/{summary.total}</span>
								</p>
								<p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">loyers payés</p>
							</div>
							<div class="text-center">
								<p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
									{formatEur(summary.totalPaye)}
								</p>
								<p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">total encaissé</p>
							</div>
							<div class="text-center">
								<p class="text-2xl font-bold {summary.solde > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}">
									{formatEur(summary.solde)}
								</p>
								<p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">solde restant</p>
							</div>
						</div>

						{#if summary.last3.length > 0}
							<div class="mt-3 border-t border-slate-200 pt-3 dark:border-slate-700">
								<p class="mb-2 text-xs font-medium text-slate-500 dark:text-slate-400">Derniers loyers</p>
								<div class="flex flex-wrap gap-2">
									{#each summary.last3 as loyer (loyer.id)}
										{@const ls = getLoyerStatut(loyer.statut)}
										<div class="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 dark:border-slate-700 dark:bg-slate-800">
											<span class="text-xs font-medium text-slate-600 dark:text-slate-300">
												{formatFrDate(loyer.date_loyer)}
											</span>
											<span class="text-xs font-medium text-slate-900 dark:text-slate-100">
												{formatEur(loyer.montant)}
											</span>
											<span class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium {ls.class}">
												{ls.label}
											</span>
										</div>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				</div>
			{/if}

			<!-- Dates -->
			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<p
						class="text-xs font-medium text-slate-500 dark:text-slate-400"
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
						class="text-xs font-medium text-slate-500 dark:text-slate-400"
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
				<div class="rounded-xl bg-slate-50 p-4 dark:bg-slate-900">
					<p
						class="text-xs font-medium text-slate-500 dark:text-slate-400"
					>
						Loyer HC
					</p>
					<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
						{formatEur(bail.loyer_hc)}
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-4 dark:bg-slate-900">
					<p
						class="text-xs font-medium text-slate-500 dark:text-slate-400"
					>
						Charges locatives
					</p>
					<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
						{formatEur(bail.charges_locatives)}
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-4 dark:bg-slate-900">
					<p
						class="text-xs font-medium text-slate-500 dark:text-slate-400"
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
						class="text-xs font-medium text-slate-500 dark:text-slate-400"
					>
						Indice de révision
					</p>
					<p class="mt-1 text-sm font-medium text-slate-900 dark:text-slate-100">
						{bail.revision_indice}
					</p>
				</div>
			{/if}

			<!-- État des lieux d'entrée -->
			{#if bail.statut === 'en_cours'}
				<div>
					<div class="flex items-center justify-between">
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
							État des lieux d'entrée
						</p>
						{#if isGerant}
							<button
								onclick={openEdlForm}
								class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
							>
								{#if bail.etat_lieux_entree}
									<Pencil class="h-3.5 w-3.5" />
									Modifier
								{:else}
									<ClipboardCheck class="h-3.5 w-3.5" />
									Renseigner
								{/if}
							</button>
						{/if}
					</div>

					{#if !bail.etat_lieux_entree && !showEdlForm}
						<div class="mt-2 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50/50 p-4 dark:border-amber-800/50 dark:bg-amber-900/10">
							<AlertTriangle class="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
							<div>
								<p class="text-sm font-medium text-amber-800 dark:text-amber-200">
									État des lieux d'entrée non renseigné
								</p>
								<p class="mt-1 text-xs text-amber-700 dark:text-amber-300">
									Obligatoire pour tout bail d'habitation (loi ALUR art. 3-2).
								</p>
							</div>
						</div>
					{:else if bail.etat_lieux_entree && !showEdlForm}
						<div class="mt-2 rounded-xl border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-700 dark:bg-slate-900/50">
							<div class="flex items-start gap-3">
								<ClipboardCheck class="mt-0.5 h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
								<div class="min-w-0 flex-1">
									<p class="text-sm font-medium text-slate-900 dark:text-slate-100">
										Réalisé le {formatFrDate(bail.etat_lieux_entree)}
									</p>
									{#if bail.etat_lieux_entree_notes}
										<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
											{bail.etat_lieux_entree_notes}
										</p>
									{/if}
									{#if bail.etat_lieux_entree_document_url}
										<a
											href={bail.etat_lieux_entree_document_url}
											target="_blank"
											rel="noopener noreferrer"
											class="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
										>
											<FileText class="h-3.5 w-3.5" />
											Voir le document
										</a>
									{/if}
								</div>
							</div>
						</div>
					{/if}

					{#if showEdlForm}
						<div class="mt-2 rounded-xl border border-sky-200 bg-sky-50/50 p-5 dark:border-sky-800/50 dark:bg-sky-950/20">
							<h3 class="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
								<ClipboardCheck class="h-4 w-4 text-sky-500" />
								État des lieux d'entrée
							</h3>
							<div class="grid gap-4 sm:grid-cols-2">
								<label class="block">
									<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Date de réalisation</span>
									<input
										type="date"
										bind:value={edlDate}
										class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
									/>
								</label>
							</div>
							<label class="mt-4 block">
								<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Notes (optionnel)</span>
								<textarea
									bind:value={edlNotes}
									rows="2"
									placeholder="Ex: RAS, quelques traces d'usure dans le salon..."
									class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
								></textarea>
							</label>
							<div class="mt-4 flex justify-end gap-2">
								<button
									onclick={() => { showEdlForm = false; }}
									class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
								>
									Annuler
								</button>
								<button
									onclick={saveEdl}
									disabled={edlSaving || !edlDate}
									class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
								>
									{#if edlSaving}<Loader2 class="h-3.5 w-3.5 animate-spin" />{/if}
									Enregistrer
								</button>
							</div>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{/if}

	<BailModal bind:open={showBailModal} {sciId} bienId={bienId} editItem={editBail} onSuccess={onRefresh} />
</div>
