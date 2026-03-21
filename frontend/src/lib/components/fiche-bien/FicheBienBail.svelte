<script lang="ts">
	import type { BailEmbed, LoyerEmbed } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { updateLocataire, cloturerBail, type ClotureBailPayload } from '$lib/api';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { Plus, Pencil, Users, Calendar, History, Mail, Phone, CheckCircle, X, Save, Lock } from 'lucide-svelte';
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
				<span
					class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium {statut.class}"
				>
					{statut.label}
				</span>
				{#if isGerant}
					<div class="flex items-center gap-2">
						{#if bail.statut === 'en_cours'}
							<button
								onclick={openClotureForm}
								class="inline-flex items-center gap-1.5 text-sm font-medium text-rose-600 transition-colors hover:text-rose-700 dark:text-rose-400 dark:hover:text-rose-300"
							>
								<Lock class="h-3.5 w-3.5" />
								Cloturer le bail
							</button>
						{/if}
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
		</div>
	{/if}

	<BailModal bind:open={showBailModal} {sciId} bienId={bienId} editItem={editBail} onSuccess={onRefresh} />
</div>
