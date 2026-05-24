<script lang="ts">
	import { getContext } from 'svelte';
	import { Building2, Users, FileText, MapPin, FolderOpen, Download, Wallet, TrendingUp, Receipt, AlertTriangle, CalendarDays, Clock, CheckCircle2, Pencil, Trash2, Loader2, ChevronDown, UserCog, Landmark, XCircle, Check, BarChart3 } from 'lucide-svelte';
	import type { SCIDetail, ComptabiliteAnnuelle, ComptabiliteMoisItem, Associe } from '$lib/api';
	import { fetchSciBiensList, exportBiensCsv, exportLoyersCsv, deleteSci, fetchComptabiliteAnnuelle, fetchComptabiliteMensuelle, changerGerant, modifierCapital, dissoudreSci, fetchSciAssociesList, marquerEcheanceFiscaleFaite, demarquerEcheanceFiscale, fetchCalendrierFiscalStatut, updateSci } from '$lib/api';
	import AnneeSelector from '$lib/components/AnneeSelector.svelte';
	import { formatEur } from '$lib/high-value/formatters';
	import { Button } from '$lib/components/ui/button';
	import { addToast } from '$lib/components/ui/toast';
	import ConfirmDeleteModal from '$lib/components/ConfirmDeleteModal.svelte';
	import RoleGate from '$lib/components/RoleGate.svelte';
	import LockedAction from '$lib/components/LockedAction.svelte';
	import SciComptabilite from '$lib/components/sci/SciComptabilite.svelte';
	import SciFiscalCalendar from '$lib/components/sci/SciFiscalCalendar.svelte';
	import type { SubscriptionEntitlements } from '$lib/api';
	import { goto } from '$app/navigation';

	const sci = getContext<SCIDetail>('sci');
	const sciId = getContext<string>('sciId');
	const userRole = getContext<string>('userRole');
	const subscription = getContext<SubscriptionEntitlements>('subscription');
	const isDemo = !subscription?.is_active;

	// svelte-ignore state_referenced_locally
	let biensCount = $state(sci.biens_count ?? sci.biens?.length ?? 0);
	let loadingBiens = $state(false);
	let exportingBiens = $state(false);
	let exportingLoyers = $state(false);

	// Delete SCI state
	let showDeleteConfirm = $state(false);
	let deletingSci = $state(false);

	// ── Gestion SCI (lifecycle) ─────────────────────────────────────
	let showGestionMenu = $state(false);

	// Changer de gérant
	let showGerantForm = $state(false);
	let gerantSaving = $state(false);
	let gerantAssocieId = $state('');
	let gerantDateEffet = $state('');
	let associesList = $state<Associe[]>([]);

	async function loadAssocies() {
		try {
			const list = await fetchSciAssociesList(sciId);
			associesList = list.filter(a => a.role !== 'gerant');
		} catch { /* ignore */ }
	}

	function openGerantForm() {
		showGestionMenu = false;
		showGerantForm = true;
		gerantDateEffet = new Date().toISOString().split('T')[0];
		gerantAssocieId = '';
		loadAssocies();
	}

	async function submitChangerGerant() {
		if (!gerantAssocieId || !gerantDateEffet) return;
		gerantSaving = true;
		try {
			await changerGerant(sciId, { associe_id: gerantAssocieId, date_effet: gerantDateEffet });
			addToast({ title: 'Gérant modifié', description: 'Le changement de gérant a été enregistré.', variant: 'success' });
			showGerantForm = false;
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de changer le gérant.', variant: 'error' });
		} finally {
			gerantSaving = false;
		}
	}

	// Modifier le capital
	let showCapitalForm = $state(false);
	let capitalSaving = $state(false);
	let capitalNouveau = $state(0);
	let capitalNbParts = $state(0);

	function openCapitalForm() {
		showGestionMenu = false;
		showCapitalForm = true;
		capitalNouveau = sci.capital_social ?? 0;
		capitalNbParts = sci.nb_parts_total ?? 0;
	}

	async function submitModifierCapital() {
		if (capitalNouveau <= 0 || capitalNbParts <= 0) return;
		capitalSaving = true;
		try {
			await modifierCapital(sciId, { nouveau_capital: capitalNouveau, nb_parts: capitalNbParts });
			addToast({ title: 'Capital modifié', description: 'Le capital social a été mis à jour.', variant: 'success' });
			showCapitalForm = false;
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de modifier le capital.', variant: 'error' });
		} finally {
			capitalSaving = false;
		}
	}

	// Dissoudre la SCI
	let showDissolutionConfirm = $state(false);
	let dissolutionSaving = $state(false);
	let dissolutionMotif = $state('');

	function openDissolutionForm() {
		showGestionMenu = false;
		showDissolutionConfirm = true;
		dissolutionMotif = '';
	}

	async function submitDissolution() {
		if (!dissolutionMotif.trim()) return;
		dissolutionSaving = true;
		try {
			await dissoudreSci(sciId, { motif: dissolutionMotif, date_dissolution: new Date().toISOString().split('T')[0] });
			addToast({ title: 'SCI dissoute', description: `${sci.nom} a été dissoute.`, variant: 'success' });
			showDissolutionConfirm = false;
			goto('/scis');
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de dissoudre la SCI.', variant: 'error' });
		} finally {
			dissolutionSaving = false;
		}
	}

	// ── Calendrier fiscal interactif (Déplacé vers SciFiscalCalendar.svelte) ─

	// ── Comptabilité (Déplacé vers SciComptabilite.svelte) ──────────

	const isGerant = $derived(userRole === 'gerant');

	// ── Jour de loyer (inline edit for SCI-level default) ─────────
	let editingJourLoyer = $state(false);
	let jourLoyerValue = $state<number | ''>(sci.jour_loyer ?? '');
	let jourLoyerSaving = $state(false);

	async function saveJourLoyer() {
		jourLoyerSaving = true;
		try {
			await updateSci(sciId, {
				jour_loyer: jourLoyerValue !== '' ? Number(jourLoyerValue) : null
			});
			addToast({ title: 'Jour de loyer mis à jour', variant: 'success' });
			editingJourLoyer = false;
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de mettre à jour le jour de loyer.', variant: 'error' });
		} finally {
			jourLoyerSaving = false;
		}
	}

	// ── Date de clôture d'exercice (inline edit) ─────────────────
	let editingCloture = $state(false);
	let clotureValue = $state<string>(sci.date_cloture_exercice ?? '');
	let clotureSaving = $state(false);

	async function saveCloture() {
		clotureSaving = true;
		try {
			await updateSci(sciId, {
				date_cloture_exercice: clotureValue || null
			});
			addToast({ title: 'Date de clôture mise à jour', variant: 'success' });
			editingCloture = false;
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de mettre à jour la date de clôture.', variant: 'error' });
		} finally {
			clotureSaving = false;
		}
	}

	const hasFinancials = $derived(
		(sci.total_monthly_rent ?? 0) > 0 || (sci.paid_loyers_total ?? 0) > 0 || (sci.total_recorded_charges ?? 0) > 0
	);
	const cashflow = $derived((sci.paid_loyers_total ?? 0) - (sci.total_recorded_charges ?? 0));
	const recouvrementTotal = $derived((sci.paid_loyers_total ?? 0) + (sci.pending_loyers_total ?? 0));
	const recouvrement = $derived(
		recouvrementTotal > 0
			? Math.round(((sci.paid_loyers_total ?? 0) / recouvrementTotal) * 100)
			: null
	);

	// ── Calendrier fiscal (Déplacé) ──────────────────────────────────────────

	async function handleDeleteSci() {
		deletingSci = true;
		try {
			await deleteSci(sciId);
			addToast({ title: 'SCI supprimée', description: `${sci.nom} a été supprimée.`, variant: 'success' });
			goto('/scis');
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de supprimer la SCI.', variant: 'error' });
		} finally {
			deletingSci = false;
			showDeleteConfirm = false;
		}
	}

	function handleExportSci() {
		const headers = ['Nom', 'SIREN', 'Régime fiscal', 'Capital social', 'Forme juridique', 'Gérant', 'RCS', 'Statut', 'Associés'];
		const row = [
			sci.nom ?? '',
			sci.siren ?? '',
			sci.regime_fiscal ?? '',
			sci.capital_social != null ? String(sci.capital_social) : '',
			sci.forme_juridique ?? '',
			sci.nom_gerant ?? '',
			[sci.rcs_numero, sci.rcs_ville].filter(Boolean).join(' ') || '',
			sci.statut ?? '',
			String(sci.associes_count ?? sci.associes?.length ?? 0)
		];
		const csvContent = [headers.join(';'), row.join(';')].join('\n');
		const blob = new Blob(['﻿' + csvContent], { type: 'text/csv;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `sci_${sci.nom}_${new Date().toISOString().slice(0, 10)}.csv`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
		addToast({ title: 'Export terminé', description: 'Le fichier CSV de la SCI a été téléchargé.', variant: 'success' });
	}

	async function handleExportBiens() {
		exportingBiens = true;
		try {
			const blob = await exportBiensCsv(sciId);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `biens_export_${new Date().toISOString().slice(0, 10)}.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			addToast({ title: 'Export terminé', description: 'Le fichier CSV des biens a été téléchargé.', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur export', description: err?.message ?? "Impossible d'exporter les biens.", variant: 'error' });
		} finally {
			exportingBiens = false;
		}
	}

	async function handleExportLoyers() {
		exportingLoyers = true;
		try {
			const blob = await exportLoyersCsv(sciId);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `loyers_export_${new Date().toISOString().slice(0, 10)}.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			addToast({ title: 'Export terminé', description: 'Le fichier CSV des loyers a été téléchargé.', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur export', description: err?.message ?? "Impossible d'exporter les loyers.", variant: 'error' });
		} finally {
			exportingLoyers = false;
		}
	}

	$effect(() => {
		if (biensCount === 0 && !sci.biens_count) {
			loadBiensCount();
		}
	});

	async function loadBiensCount() {
		loadingBiens = true;
		try {
			const list = await fetchSciBiensList(sciId);
			biensCount = list.length;
		} catch {
			// keep the default count
		} finally {
			loadingBiens = false;
		}
	}

	const quickLinks = $derived([
		{
			href: `/scis/${sciId}/biens`,
			icon: MapPin,
			iconClass: 'text-blue-600 dark:text-blue-400',
			bgClass: 'bg-blue-50 dark:bg-blue-950/40',
			value: biensCount,
			label: 'Biens',
			loading: loadingBiens
		},
		{
			href: `/scis/${sciId}/associes`,
			icon: Users,
			iconClass: 'text-purple-600 dark:text-purple-400',
			bgClass: 'bg-purple-50 dark:bg-purple-950/40',
			value: sci.associes_count ?? sci.associes?.length ?? 0,
			label: 'Associés',
			loading: false
		},
		{
			href: `/scis/${sciId}/fiscalite`,
			icon: FileText,
			iconClass: 'text-amber-600 dark:text-amber-400',
			bgClass: 'bg-amber-50 dark:bg-amber-950/40',
			value: sci.regime_fiscal ?? '—',
			label: 'Régime fiscal',
			loading: false
		},
		{
			href: `/scis/${sciId}/documents`,
			icon: FolderOpen,
			iconClass: 'text-teal-600 dark:text-teal-400',
			bgClass: 'bg-teal-50 dark:bg-teal-950/40',
			value: (sci as any).documents?.length ?? 0,
			label: 'Documents',
			loading: false
		}
	]);
</script>

<svelte:head><title>{sci.nom} | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">SCI</p>
		<div class="flex flex-wrap items-start justify-between gap-4">
			<div>
				<h1 class="sci-page-title">{sci.nom}</h1>
				{#if sci.siren}
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">SIREN {sci.siren}</p>
				{/if}
			</div>
			<div class="flex flex-wrap items-center gap-2">
				<span class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium {userRole === 'gerant'
					? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
					: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'}">
					{userRole === 'gerant' ? 'Gérant' : 'Associé'}
				</span>
				{#if sci.statut}
					<span class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-400">
						{#if sci.statut === 'configuration'}À structurer{:else if sci.statut === 'mise_en_service'}Mise en service{:else}En exploitation{/if}
					</span>
				{/if}
				<RoleGate>
					<LockedAction {isDemo} action="modifier la SCI">
						<a
							href={`/scis/${sciId}/settings`}
							class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							<Pencil class="h-3.5 w-3.5" />
							Modifier
						</a>
					</LockedAction>
					<LockedAction {isDemo} action="supprimer la SCI">
						<button
							onclick={() => { showDeleteConfirm = true; }}
							class="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-sm font-medium text-rose-600 transition-colors hover:bg-rose-50 dark:border-rose-800 dark:bg-slate-900 dark:text-rose-400 dark:hover:bg-rose-950/30"
							title="Supprimer la SCI"
						>
							<Trash2 class="h-3.5 w-3.5" />
							Supprimer
						</button>
					</LockedAction>
					<!-- Gestion dropdown -->
					<LockedAction {isDemo} action="gérer la SCI">
						<div class="relative">
							<button
								onclick={() => { showGestionMenu = !showGestionMenu; }}
								class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
							>
								Gestion
								<ChevronDown class="h-3.5 w-3.5" />
							</button>
						{#if showGestionMenu}
							<!-- svelte-ignore a11y_click_events_have_key_events -->
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<div class="fixed inset-0 z-40" onclick={() => { showGestionMenu = false; }}></div>
							<div class="absolute right-0 top-full z-50 mt-1 w-56 rounded-xl border border-slate-200 bg-white py-1 shadow-xl dark:border-slate-700 dark:bg-slate-900">
								<button onclick={openGerantForm} class="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800">
									<UserCog class="h-4 w-4 flex-shrink-0 text-indigo-500" />
									Changer de gérant
								</button>
								<button onclick={openCapitalForm} class="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800">
									<Landmark class="h-4 w-4 flex-shrink-0 text-sky-500" />
									Modifier le capital
								</button>
								<div class="my-1 border-t border-slate-100 dark:border-slate-800"></div>
								<button onclick={openDissolutionForm} class="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-sm text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/30">
									<XCircle class="h-4 w-4 flex-shrink-0" />
									Dissoudre la SCI
								</button>
							</div>
						{/if}
					</div>
					</LockedAction>
				</RoleGate>
			</div>
		</div>
	</header>

	<!-- Navigation rapide -->
	<div class="sci-stagger grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#each quickLinks as link}
			<a
				href={link.href}
				class="group rounded-2xl border border-slate-200 bg-white p-5 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700"
			>
				<div class="flex items-center gap-3">
					<div class="flex h-10 w-10 items-center justify-center rounded-xl {link.bgClass}">
						<link.icon class="h-5 w-5 {link.iconClass}" />
					</div>
					<div class="min-w-0">
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">{link.label}</p>
						<p class="text-xl font-bold text-slate-900 dark:text-slate-100">
							{#if link.loading}
								<span class="inline-flex h-6 w-8 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></span>
							{:else}
								{link.value}
							{/if}
						</p>
					</div>
				</div>
			</a>
		{/each}
	</div>

	<!-- KPIs financiers -->
	{#if hasFinancials}
		<div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
			<div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
				<div class="flex items-center gap-3">
					<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-50 dark:bg-sky-950/40">
						<Receipt class="h-5 w-5 text-sky-600 dark:text-sky-400" />
					</div>
					<div>
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Loyer cible / mois</p>
						<p class="text-xl font-bold text-slate-900 dark:text-slate-100">{formatEur(sci.total_monthly_rent ?? 0)}</p>
					</div>
				</div>
			</div>
			<div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
				<div class="flex items-center gap-3">
					<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 dark:bg-emerald-950/40">
						<Wallet class="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
					</div>
					<div>
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Loyers encaissés</p>
						<p class="text-xl font-bold text-emerald-700 dark:text-emerald-300">{formatEur(sci.paid_loyers_total ?? 0)}</p>
					</div>
				</div>
			</div>
			<div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
				<div class="flex items-center gap-3">
					<div class="flex h-10 w-10 items-center justify-center rounded-xl {cashflow >= 0 ? 'bg-emerald-50 dark:bg-emerald-950/40' : 'bg-rose-50 dark:bg-rose-950/40'}">
						<TrendingUp class="h-5 w-5 {cashflow >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}" />
					</div>
					<div>
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Cashflow net</p>
						<p class="text-xl font-bold {cashflow >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}">{formatEur(cashflow)}</p>
					</div>
				</div>
			</div>
			<div class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
				<div class="flex items-center gap-3">
					<div class="flex h-10 w-10 items-center justify-center rounded-xl {(recouvrement ?? 0) >= 80 ? 'bg-emerald-50 dark:bg-emerald-950/40' : 'bg-amber-50 dark:bg-amber-950/40'}">
						<TrendingUp class="h-5 w-5 {(recouvrement ?? 0) >= 80 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}" />
					</div>
					<div>
						<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Recouvrement</p>
						<p class="text-xl font-bold text-slate-900 dark:text-slate-100">
							{recouvrement != null ? `${recouvrement}%` : '—'}
						</p>
					</div>
				</div>
			</div>
		</div>
	{:else if biensCount > 0}
		<div class="mt-6 rounded-2xl border border-dashed border-amber-300 bg-amber-50/50 p-5 dark:border-amber-800 dark:bg-amber-950/20">
			<div class="flex items-start gap-3">
				<AlertTriangle class="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-500" />
				<div>
					<p class="text-sm font-medium text-amber-800 dark:text-amber-200">Données financières en attente</p>
					<p class="mt-1 text-sm text-amber-700 dark:text-amber-300">
						Enregistrez des loyers et charges pour voir les KPIs financiers de cette SCI.
					</p>
					<a href={`/scis/${sciId}/biens`} class="mt-2 inline-flex text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400">
						Accéder aux biens →
					</a>
				</div>
			</div>
		</div>
	{/if}

	<!-- Calendrier fiscal -->
	<SciFiscalCalendar {sciId} {sci} />

	<SciComptabilite {sciId} {sci} />

	<!-- Informations de la SCI -->
	<div class="mt-6 grid gap-4 lg:grid-cols-2">
		<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
			<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Gouvernance</h2>
			<div class="mt-4 grid gap-3">
				<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
					<span class="text-sm text-slate-500 dark:text-slate-400">Votre rôle</span>
					<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{isGerant ? 'Gérant' : 'Associé'}</span>
				</div>
				{#if sci.user_part != null}
					<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
						<span class="text-sm text-slate-500 dark:text-slate-400">Part détenue</span>
						<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{sci.user_part}%</span>
					</div>
				{/if}
				<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
					<span class="text-sm text-slate-500 dark:text-slate-400">Régime fiscal</span>
					<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{sci.regime_fiscal ?? '—'}</span>
				</div>
				<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
					<span class="text-sm text-slate-500 dark:text-slate-400">Associés</span>
					<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{sci.associes_count ?? sci.associes?.length ?? 0}</span>
				</div>
				{#if sci.capital_social}
					<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
						<span class="text-sm text-slate-500 dark:text-slate-400">Capital social</span>
						<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{formatEur(sci.capital_social)}</span>
					</div>
				{/if}
				{#if sci.nom_gerant}
					<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
						<span class="text-sm text-slate-500 dark:text-slate-400">Gérant</span>
						<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{sci.nom_gerant}</span>
					</div>
				{/if}
				{#if sci.rcs_numero || sci.rcs_ville}
					<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
						<span class="text-sm text-slate-500 dark:text-slate-400">RCS</span>
						<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{[sci.rcs_numero, sci.rcs_ville].filter(Boolean).join(' — ')}</span>
					</div>
				{/if}
				{#if sci.forme_juridique}
					<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
						<span class="text-sm text-slate-500 dark:text-slate-400">Forme juridique</span>
						<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{sci.forme_juridique}</span>
					</div>
				{/if}
				<!-- Jour de loyer par défaut (SCI-level override) -->
				<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
					<span class="text-sm text-slate-500 dark:text-slate-400">Jour de loyer</span>
					{#if editingJourLoyer && isGerant}
						<div class="flex items-center gap-2">
							<input
								type="number"
								min="1"
								max="28"
								bind:value={jourLoyerValue}
								class="w-16 rounded-lg border border-slate-200 bg-white px-2 py-1 text-right text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
								placeholder="1"
							/>
							<span class="text-xs text-slate-500 dark:text-slate-400">du mois</span>
							<button
								onclick={saveJourLoyer}
								disabled={jourLoyerSaving}
								class="rounded-lg bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
							>
								{jourLoyerSaving ? '…' : 'OK'}
							</button>
							<button
								onclick={() => { editingJourLoyer = false; jourLoyerValue = sci.jour_loyer ?? ''; }}
								class="rounded-lg px-2 py-1 text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
							>
								✕
							</button>
						</div>
					{:else}
						<div class="flex items-center gap-2">
							<span class="text-sm font-medium text-slate-900 dark:text-slate-100">
								{sci.jour_loyer != null ? `${sci.jour_loyer} du mois` : 'Hérité du réglage global'}
							</span>
							{#if isGerant}
								<button
									onclick={() => { editingJourLoyer = true; jourLoyerValue = sci.jour_loyer ?? ''; }}
									class="rounded p-1 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400"
									title="Modifier le jour de loyer"
								>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
								</button>
							{/if}
						</div>
					{/if}
				</div>
				<!-- Date de clôture d'exercice -->
				<div class="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-900">
					<span class="text-sm text-slate-500 dark:text-slate-400">Clôture d'exercice</span>
					{#if editingCloture && isGerant}
						<div class="flex items-center gap-2">
							<input
								type="date"
								bind:value={clotureValue}
								class="rounded-lg border border-slate-200 bg-white px-2 py-1 text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
							/>
							<button
								onclick={saveCloture}
								disabled={clotureSaving}
								class="rounded-lg bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
							>
								{clotureSaving ? '…' : 'OK'}
							</button>
							<button
								onclick={() => { editingCloture = false; clotureValue = sci.date_cloture_exercice ?? ''; }}
								class="rounded-lg px-2 py-1 text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
							>
								✕
							</button>
						</div>
					{:else}
						<div class="flex items-center gap-2">
							<span class="text-sm font-medium text-slate-900 dark:text-slate-100">
								{sci.date_cloture_exercice
									? new Date(sci.date_cloture_exercice).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })
									: '31 décembre'}
							</span>
							{#if isGerant}
								<button
									onclick={() => { editingCloture = true; clotureValue = sci.date_cloture_exercice ?? ''; }}
									class="rounded p-1 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400"
									title="Modifier la date de clôture d'exercice"
								>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
								</button>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>

		<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
			<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Exports</h2>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Télécharger les données de cette SCI au format CSV.</p>
			<LockedAction {isDemo} action="exporter les données CSV">
				<div class="mt-4 grid gap-3">
					<Button onclick={handleExportSci} variant="outline" class="justify-start" title="Exporte les informations générales de la SCI (nom, SIREN, régime fiscal, associés, capital)">
						<Download class="mr-2 h-4 w-4" />
						Export SCI (CSV)
					</Button>
					<Button onclick={handleExportBiens} disabled={exportingBiens} variant="outline" class="justify-start" title="Exporte la liste des biens immobiliers (adresse, type, surface, loyer)">
						<Download class="mr-2 h-4 w-4" />
						{exportingBiens ? 'Export en cours...' : 'Export Biens (CSV)'}
					</Button>
					<Button onclick={handleExportLoyers} disabled={exportingLoyers} variant="outline" class="justify-start" title="Exporte l'historique des loyers (montant, statut, date de paiement)">
						<Download class="mr-2 h-4 w-4" />
						{exportingLoyers ? 'Export en cours...' : 'Export Loyers (CSV)'}
					</Button>
					<Button href={`/bilans?scope=sci&scope_id=${sciId}`} variant="outline" class="justify-start" title="Bilan mensuel comptable de cette SCI">
						<FileText class="mr-2 h-4 w-4" />
						Bilan mensuel
					</Button>
				</div>
			</LockedAction>
		</div>
	</div>

	<!-- Changer de gérant -->
	{#if showGerantForm}
		<div class="mt-6 rounded-2xl border border-indigo-200 bg-indigo-50/50 p-6 dark:border-indigo-800/50 dark:bg-indigo-950/20">
			<h3 class="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
				<UserCog class="h-4 w-4 text-indigo-500" />
				Changer de gérant
			</h3>
			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<label for="gerant-associe" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Nouvel associé gérant</label>
					<select
						id="gerant-associe"
						bind:value={gerantAssocieId}
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					>
						<option value="">Sélectionner un associé</option>
						{#each associesList as associe}
							<option value={String(associe.id)}>{associe.nom} ({associe.email ?? 'pas d\'email'})</option>
						{/each}
					</select>
				</div>
				<div>
					<label for="gerant-date" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Date d'effet</label>
					<input
						id="gerant-date"
						type="date"
						bind:value={gerantDateEffet}
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
			</div>
			<div class="mt-4 flex items-center justify-end gap-2">
				<button onclick={() => { showGerantForm = false; }} class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800">
					Annuler
				</button>
				<button
					onclick={submitChangerGerant}
					disabled={gerantSaving || !gerantAssocieId}
					class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
				>
					{#if gerantSaving}<Loader2 class="h-4 w-4 animate-spin" />{/if}
					Confirmer le changement
				</button>
			</div>
		</div>
	{/if}

	<!-- Modifier le capital -->
	{#if showCapitalForm}
		<div class="mt-6 rounded-2xl border border-sky-200 bg-sky-50/50 p-6 dark:border-sky-800/50 dark:bg-sky-950/20">
			<h3 class="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
				<Landmark class="h-4 w-4 text-sky-500" />
				Modifier le capital social
			</h3>
			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<label for="capital-montant" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Nouveau capital social</label>
					<input
						id="capital-montant"
						type="number"
						min="1"
						bind:value={capitalNouveau}
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
				<div>
					<label for="capital-parts" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Nombre de parts</label>
					<input
						id="capital-parts"
						type="number"
						min="1"
						bind:value={capitalNbParts}
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
			</div>
			{#if capitalNbParts > 0 && capitalNouveau > 0}
				<p class="mt-3 text-sm text-slate-500 dark:text-slate-400">
					Valeur nominale par part : <span class="font-semibold text-slate-700 dark:text-slate-200">{formatEur(capitalNouveau / capitalNbParts)}</span>
				</p>
			{/if}
			<div class="mt-4 flex items-center justify-end gap-2">
				<button onclick={() => { showCapitalForm = false; }} class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800">
					Annuler
				</button>
				<button
					onclick={submitModifierCapital}
					disabled={capitalSaving || capitalNouveau <= 0 || capitalNbParts <= 0}
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
				>
					{#if capitalSaving}<Loader2 class="h-4 w-4 animate-spin" />{/if}
					Mettre à jour
				</button>
			</div>
		</div>
	{/if}

	<!-- Dissolution SCI Confirmation -->
	{#if showDissolutionConfirm}
		<div
			role="alertdialog"
			aria-modal="true"
			aria-labelledby="dissolution-title"
			class="fixed inset-0 z-50 flex items-center justify-center p-4"
		>
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick={() => { if (!dissolutionSaving) showDissolutionConfirm = false; }}></div>
			<div class="relative w-full max-w-[460px] rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-900">
				<div class="flex items-start gap-3">
					<div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-rose-100 dark:bg-rose-900/40">
						<XCircle class="h-5 w-5 text-rose-600 dark:text-rose-400" />
					</div>
					<div class="flex-1">
						<h2 id="dissolution-title" class="text-base font-semibold text-slate-900 dark:text-slate-100">Dissoudre {sci.nom} ?</h2>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							Cette action enregistrera la dissolution de la SCI. Tous les biens devront être cédés ou transférés au préalable.
						</p>
						<div class="mt-4">
							<label for="dissolution-motif" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Motif de dissolution</label>
							<textarea
								id="dissolution-motif"
								bind:value={dissolutionMotif}
								rows="3"
								placeholder="Ex : Fin d'activité, vente de tous les biens..."
								class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
							></textarea>
						</div>
					</div>
				</div>
				<div class="mt-5 flex items-center justify-end gap-2">
					<button onclick={() => { showDissolutionConfirm = false; }} disabled={dissolutionSaving}
						class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800">
						Annuler
					</button>
					<button onclick={submitDissolution} disabled={dissolutionSaving || !dissolutionMotif.trim()}
						class="inline-flex items-center gap-2 rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50">
						{#if dissolutionSaving}<Loader2 class="h-4 w-4 animate-spin" />{/if}
						Dissoudre la SCI
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Delete SCI Confirmation Modal -->
	<ConfirmDeleteModal
		open={showDeleteConfirm}
		entityName={sci.nom}
		entityType="cette SCI"
		warningMessage="Cette action supprimera définitivement {biensCount} bien{biensCount > 1 ? 's' : ''}, {sci.associes_count ?? sci.associes?.length ?? 0} associé{(sci.associes_count ?? sci.associes?.length ?? 0) > 1 ? 's' : ''}, {sci.loyers_count ?? 0} loyer{(sci.loyers_count ?? 0) > 1 ? 's' : ''}, {sci.charges_count ?? 0} charge{(sci.charges_count ?? 0) > 1 ? 's' : ''}, ainsi que tous les baux, documents et quittances associés. Cette action est irréversible."
		loading={deletingSci}
		onConfirm={handleDeleteSci}
		onCancel={() => { showDeleteConfirm = false; }}
	/>
</section>
