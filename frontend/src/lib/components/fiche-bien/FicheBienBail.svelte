<script lang="ts">
	import type { BailEmbed, LoyerEmbed } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { Plus, Pencil, Users, Calendar, History, Mail, Phone, CheckCircle } from 'lucide-svelte';
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
					<button
						onclick={() => openBailModal(bail)}
						class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
					>
						<Pencil class="h-3.5 w-3.5" />
						Modifier
					</button>
				{/if}
			</div>

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
												<a
													href="mailto:{loc.email}"
													class="inline-flex items-center gap-1.5 text-sm text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
												>
													<Mail class="h-3.5 w-3.5" />
													{loc.email}
												</a>
											{/if}
											{#if loc.telephone}
												<a
													href="tel:{loc.telephone}"
													class="inline-flex items-center gap-1.5 text-sm text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
												>
													<Phone class="h-3.5 w-3.5" />
													{loc.telephone}
												</a>
											{/if}
										</div>
									</div>
									<!-- Contact rapide -->
									<div class="flex shrink-0 items-center gap-1.5">
										{#if loc.email}
											<a
												href="mailto:{loc.email}"
												class="rounded-lg border border-slate-200 bg-white p-2 text-slate-500 transition-colors hover:border-sky-300 hover:text-sky-600 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-sky-700 dark:hover:text-sky-400"
												title="Envoyer un email"
												aria-label="Envoyer un email à {loc.prenom ? `${loc.prenom} ${loc.nom}` : loc.nom}"
											>
												<Mail class="h-4 w-4" />
											</a>
										{/if}
										{#if loc.telephone}
											<a
												href="tel:{loc.telephone}"
												class="rounded-lg border border-slate-200 bg-white p-2 text-slate-500 transition-colors hover:border-sky-300 hover:text-sky-600 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-sky-700 dark:hover:text-sky-400"
												title="Appeler"
												aria-label="Appeler {loc.prenom ? `${loc.prenom} ${loc.nom}` : loc.nom}"
											>
												<Phone class="h-4 w-4" />
											</a>
										{/if}
									</div>
								</div>
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
