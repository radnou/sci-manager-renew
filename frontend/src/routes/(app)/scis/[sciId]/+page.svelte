<script lang="ts">
	import { getContext } from 'svelte';
	import { Building2, Users, FileText, MapPin, FolderOpen, Download, Wallet, TrendingUp, Receipt, AlertTriangle, CalendarDays, Clock, CheckCircle2, Pencil, Trash2, Loader2, ChevronDown, UserCog, Landmark, XCircle, Check, BarChart3 } from 'lucide-svelte';
	import type { SCIDetail, ComptabiliteAnnuelle, ComptabiliteMoisItem, Associe } from '$lib/api';
	import { fetchSciBiensList, exportBiensCsv, exportLoyersCsv, deleteSci, fetchComptabiliteAnnuelle, fetchComptabiliteMensuelle, changerGerant, modifierCapital, dissoudreSci, fetchSciAssociesList, marquerEcheanceFiscaleFaite, demarquerEcheanceFiscale, fetchCalendrierFiscalStatut } from '$lib/api';
	import AnneeSelector from '$lib/components/AnneeSelector.svelte';
	import { formatEur } from '$lib/high-value/formatters';
	import { Button } from '$lib/components/ui/button';
	import { addToast } from '$lib/components/ui/toast';
	import ConfirmDeleteModal from '$lib/components/ConfirmDeleteModal.svelte';
	import RoleGate from '$lib/components/RoleGate.svelte';
	import LockedAction from '$lib/components/LockedAction.svelte';
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

	// ── Calendrier fiscal interactif ───────────────────────────────
	let fiscalDoneMap = $state<Record<string, boolean>>({});

	$effect(() => {
		loadFiscalStatut(currentYear);
	});

	async function loadFiscalStatut(annee: number) {
		try {
			fiscalDoneMap = await fetchCalendrierFiscalStatut(sciId, annee);
		} catch {
			fiscalDoneMap = {};
		}
	}

	async function toggleFiscalDone(key: string) {
		const wasDone = fiscalDoneMap[key] ?? false;
		// Optimistic update
		fiscalDoneMap = { ...fiscalDoneMap, [key]: !wasDone };
		try {
			if (wasDone) {
				await demarquerEcheanceFiscale(sciId, currentYear, key);
			} else {
				await marquerEcheanceFiscaleFaite(sciId, currentYear, key);
			}
		} catch {
			// Rollback
			fiscalDoneMap = { ...fiscalDoneMap, [key]: wasDone };
			addToast({ title: 'Erreur', description: 'Impossible de mettre à jour le statut.', variant: 'error' });
		}
	}

	// ── Comptabilité annuelle ──────────────────────────────────────
	let comptaYear = $state(new Date().getFullYear());
	let comptaData = $state<ComptabiliteAnnuelle | null>(null);
	let comptaLoading = $state(false);
	let comptaError = $state('');

	$effect(() => {
		loadComptabilite(comptaYear);
	});

	async function loadComptabilite(annee: number) {
		comptaLoading = true;
		comptaError = '';
		try {
			comptaData = await fetchComptabiliteAnnuelle(sciId, annee);
		} catch (err: any) {
			comptaError = err?.message ?? 'Impossible de charger la comptabilité.';
			comptaData = null;
		} finally {
			comptaLoading = false;
		}
	}

	function handleComptaYearChange(year: number) {
		comptaYear = year;
	}

	function exportComptaCsv() {
		if (!comptaData) return;
		const headers = ['Bien', 'Revenus', 'Charges', 'Événements', 'Résultat'];
		const rows = (comptaData.biens || []).map(l => [
			l.adresse,
			l.revenus.toFixed(2),
			l.charges.toFixed(2),
			l.evenements_deductibles.toFixed(2),
			l.resultat.toFixed(2)
		]);
		rows.push([
			'TOTAL',
			comptaData.totaux?.revenus.toFixed(2),
			comptaData.totaux?.charges.toFixed(2),
			comptaData.totaux?.evenements_deductibles.toFixed(2),
			comptaData.totaux?.resultat.toFixed(2)
		]);
		const csvContent = [headers.join(';'), ...rows.map(r => r.join(';'))].join('\n');
		const blob = new Blob(['﻿' + csvContent], { type: 'text/csv;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `comptabilite_${sci.nom}_${comptaYear}.csv`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}

	function formatVariation(value: number | null | undefined): { text: string; color: string } | null {
		if (value == null || value === 0) return null;
		const pct = Math.round(value);
		return {
			text: pct > 0 ? `+${pct}%` : `${pct}%`,
			color: pct > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
		};
	}

	const comptaVarRevenus = $derived(comptaData ? formatVariation(comptaData.variation_n1?.revenus) : null);
	const comptaVarCharges = $derived(comptaData ? formatVariation(comptaData.variation_n1?.charges) : null);
	const comptaVarResultat = $derived(comptaData ? formatVariation(comptaData.variation_n1?.resultat) : null);

	// ── Vue mensuelle comptabilité ────────────────────────────────
	let comptaView = $state<'annuel' | 'mensuel'>('annuel');
	let mensuelData = $state<ComptabiliteMoisItem[]>([]);
	let mensuelLoading = $state(false);
	let mensuelError = $state('');

	const mensuelMax = $derived(
		Math.max(1, ...mensuelData.map(m => Math.max(m.revenus, m.charges)))
	);

	const MOIS_LABELS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'];

	$effect(() => {
		if (comptaView === 'mensuel') {
			loadMensuel(comptaYear);
		}
	});

	async function loadMensuel(annee: number) {
		mensuelLoading = true;
		mensuelError = '';
		try {
			mensuelData = await fetchComptabiliteMensuelle(sciId, annee);
		} catch (err: any) {
			mensuelError = err?.message ?? 'Impossible de charger les données mensuelles.';
			mensuelData = [];
		} finally {
			mensuelLoading = false;
		}
	}

	const isGerant = $derived(userRole === 'gerant');
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

	// ── Calendrier fiscal ──────────────────────────────────────────
	type FiscalEvent = {
		key: string;
		label: string;
		date: Date;
		regime: string | null;
		description: string;
	};

	const currentYear = new Date().getFullYear();
	const regime = (sci.regime_fiscal ?? '').toUpperCase();

	// Dynamic fiscal calendar based on exercise closing date
	const clotureRaw = (sci as any).date_cloture_exercice as string | undefined;
	const clotureDate = clotureRaw ? new Date(clotureRaw) : null;
	const clotureMonth = clotureDate ? clotureDate.getMonth() : 11; // default: December (month 11)
	const clotureDay = clotureDate ? clotureDate.getDate() : 31;
	const clotureLabel = clotureDate
		? clotureDate.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })
		: null;

	function addMonths(date: Date, months: number): Date {
		const d = new Date(date);
		d.setMonth(d.getMonth() + months);
		return d;
	}

	const clotureRef = new Date(currentYear, clotureMonth, clotureDay);
	const agDate = addMonths(clotureRef, 6);
	const liasseIsDate = addMonths(clotureRef, 3);

	// V14 — CFE conditional on type_locatif
	const biensList = (sci.biens ?? []) as Array<{ type_locatif?: string | null }>;
	const hasCfeBiens = biensList.some(b => b.type_locatif === 'meuble' || b.type_locatif === 'commercial' || b.type_locatif === 'mixte');

	const allDeadlines: FiscalEvent[] = [
		...(regime === 'IR' ? [
			{ key: 'declaration_2072', label: 'Déclaration 2072', date: new Date(currentYear, 4, 20), regime: 'IR', description: 'Déclaration des résultats de la SCI à l\'IR' },
			{ key: 'declaration_2044', label: 'Déclaration 2044', date: new Date(currentYear, 4, 31), regime: 'IR', description: 'Déclaration individuelle des revenus fonciers (chaque associé)' },
		] : []),
		...(regime === 'IS' ? [
			{ key: 'liasse_fiscale_is', label: 'Liasse fiscale IS', date: liasseIsDate, regime: 'IS', description: `Liasse fiscale pour SCI à l'IS (3 mois post-clôture)${clotureLabel ? ` — basé sur la clôture au ${clotureLabel}` : ''}` },
		] : []),
		{ key: 'ag_annuelle', label: 'AG annuelle', date: agDate, regime: null, description: `Assemblée générale obligatoire (6 mois post-clôture)${clotureLabel ? ` — basé sur la clôture au ${clotureLabel}` : ''}` },
		{ key: 'taxe_fonciere', label: 'Taxe foncière', date: new Date(currentYear, 9, 15), regime: null, description: 'Paiement de la taxe foncière' },
		// svelte-ignore state_referenced_locally
		...(hasCfeBiens ? [
			{ key: 'cfe', label: 'CFE', date: new Date(currentYear, 11, 15), regime: null, description: 'Cotisation Foncière des Entreprises' },
		] : biensCount > 0 ? [
			{ key: 'cfe', label: 'CFE', date: new Date(currentYear, 11, 15), regime: null, description: 'Exonéré (biens nus résidentiels)' },
		] : []),
	];

	const now = new Date();
	const fiscalEvents = $derived(
		allDeadlines
			.map(e => ({ ...e, daysUntil: Math.ceil((e.date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)) }))
			.sort((a, b) => a.date.getTime() - b.date.getTime())
	);

	function deadlineStatus(daysUntil: number): { color: string; iconColor: string; bg: string; label: string } {
		if (daysUntil < 0) return { color: 'text-slate-400 dark:text-slate-500', iconColor: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-950/30', label: 'Passé' };
		if (daysUntil <= 15) return { color: 'text-rose-700 dark:text-rose-300', iconColor: 'text-rose-500', bg: 'bg-rose-50 dark:bg-rose-950/30', label: `${daysUntil}j` };
		if (daysUntil <= 45) return { color: 'text-amber-700 dark:text-amber-300', iconColor: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-950/30', label: `${daysUntil}j` };
		return { color: 'text-slate-600 dark:text-slate-400', iconColor: 'text-slate-400', bg: 'bg-slate-50 dark:bg-slate-900', label: `${daysUntil}j` };
	}

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
			<div class="flex items-center gap-2">
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
	<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="flex items-center gap-2">
			<CalendarDays class="h-5 w-5 text-sky-600 dark:text-sky-400" />
			<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Calendrier fiscal {currentYear}</h2>
			{#if regime}
				<span class="rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">{regime}</span>
			{/if}
		</div>
		<div class="mt-4 space-y-2">
			{#each fiscalEvents as event}
				{@const status = deadlineStatus(event.daysUntil)}
				{@const isDone = fiscalDoneMap[event.key] ?? false}
				<div class="flex items-center gap-3 rounded-xl {isDone ? 'bg-emerald-50 dark:bg-emerald-950/30' : status.bg} px-4 py-3">
					<button
						type="button"
						onclick={() => toggleFiscalDone(event.key)}
						class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-white/80 transition-colors hover:bg-white dark:bg-slate-800/80 dark:hover:bg-slate-700/80"
						title={isDone ? 'Marquer comme non fait' : 'Marquer comme fait'}
						aria-label={isDone ? `${event.label} : fait` : `${event.label} : en attente`}
					>
						{#if isDone}
							<Check class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
						{:else if event.daysUntil < 0}
							<CheckCircle2 class="h-4 w-4 {status.iconColor}" />
						{:else}
							<Clock class="h-4 w-4 {status.iconColor}" />
						{/if}
					</button>
					<div class="min-w-0 flex-1">
						<div class="flex items-center justify-between gap-2">
							<p class="text-sm font-medium {isDone ? 'text-emerald-700 line-through dark:text-emerald-400' : event.daysUntil < 0 ? 'text-slate-400 dark:text-slate-500' : 'text-slate-900 dark:text-slate-100'}">
								{event.label}
								{#if isDone}
									<span class="ml-1.5 text-xs font-normal text-emerald-600 dark:text-emerald-400">fait</span>
								{/if}
							</p>
							<span class="flex-shrink-0 text-xs font-semibold {isDone ? 'text-emerald-600 dark:text-emerald-400' : status.color}">
								{isDone ? 'Fait' : status.label}
							</span>
						</div>
						<p class="text-xs {isDone ? 'text-emerald-600/70 dark:text-emerald-400/70' : event.daysUntil < 0 ? 'text-slate-400 dark:text-slate-500' : 'text-slate-500 dark:text-slate-400'}">
							{event.date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} — {event.description}
						</p>
					</div>
				</div>
			{/each}
		</div>
		{#if !regime}
			<p class="mt-3 text-xs text-amber-600 dark:text-amber-400">
				Renseignez le régime fiscal (IR/IS) de cette SCI pour afficher les échéances spécifiques.
			</p>
		{/if}
	</div>

	<!-- Comptabilité annuelle / mensuelle -->
	<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="flex flex-wrap items-center justify-between gap-3">
			<div class="flex flex-wrap items-center gap-2">
				<Wallet class="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
				<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Comptabilité</h2>
				<AnneeSelector value={comptaYear} onchange={handleComptaYearChange} />
				<!-- Toggle Annuel / Mensuel -->
				<div class="ml-2 inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 dark:border-slate-700 dark:bg-slate-800" role="radiogroup" aria-label="Vue comptabilité">
					<button
						type="button"
						role="radio"
						aria-checked={comptaView === 'annuel'}
						onclick={() => { comptaView = 'annuel'; }}
						class="rounded-md px-3 py-1 text-xs font-medium transition-colors {comptaView === 'annuel'
							? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-slate-100'
							: 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						Annuel
					</button>
					<button
						type="button"
						role="radio"
						aria-checked={comptaView === 'mensuel'}
						onclick={() => { comptaView = 'mensuel'; }}
						class="inline-flex items-center gap-1 rounded-md px-3 py-1 text-xs font-medium transition-colors {comptaView === 'mensuel'
							? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-slate-100'
							: 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
					>
						<BarChart3 class="h-3 w-3" />
						Mensuel
					</button>
				</div>
			</div>
			{#if comptaView === 'annuel' && comptaData && (comptaData.biens || []).length > 0}
				<button
					type="button"
					onclick={exportComptaCsv}
					class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
				>
					<Download class="h-3.5 w-3.5" />
					Exporter (CSV)
				</button>
			{/if}
		</div>

		{#if comptaView === 'annuel'}
			<!-- Vue annuelle (existante) -->
			{#if comptaLoading}
				<div class="mt-4 flex items-center justify-center py-8">
					<Loader2 class="h-5 w-5 animate-spin text-slate-400" />
				</div>
			{:else if comptaError}
				<p class="mt-4 text-sm text-rose-600 dark:text-rose-400">{comptaError}</p>
			{:else if comptaData && (comptaData.biens || []).length > 0}
				<div class="mt-4 overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-slate-200 dark:border-slate-700">
								<th class="pb-2 text-left font-semibold text-slate-600 dark:text-slate-400">Bien</th>
								<th class="pb-2 text-right font-semibold text-slate-600 dark:text-slate-400">Revenus</th>
								<th class="pb-2 text-right font-semibold text-slate-600 dark:text-slate-400">Charges</th>
								<th class="pb-2 text-right font-semibold text-slate-600 dark:text-slate-400">Événements</th>
								<th class="pb-2 text-right font-semibold text-slate-600 dark:text-slate-400">Résultat</th>
							</tr>
						</thead>
						<tbody>
							{#each (comptaData.biens || []) as ligne}
								<tr class="border-b border-slate-100 dark:border-slate-800">
									<td class="py-2.5 font-medium text-slate-900 dark:text-slate-100">{ligne.adresse}</td>
									<td class="py-2.5 text-right text-slate-700 dark:text-slate-300">{formatEur(ligne.revenus)}</td>
									<td class="py-2.5 text-right text-slate-700 dark:text-slate-300">{formatEur(ligne.charges)}</td>
									<td class="py-2.5 text-right text-slate-700 dark:text-slate-300">{formatEur(ligne.evenements_deductibles)}</td>
									<td class="py-2.5 text-right font-semibold {ligne.resultat >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}">{formatEur(ligne.resultat)}</td>
								</tr>
							{/each}
						</tbody>
						<tfoot>
							<tr class="border-t-2 border-slate-300 dark:border-slate-600">
								<td class="pt-3 font-bold text-slate-900 dark:text-slate-100">Total</td>
								<td class="pt-3 text-right font-bold text-slate-900 dark:text-slate-100">
									{formatEur(comptaData.totaux?.revenus)}
									{#if comptaVarRevenus}<span class="ml-1 text-xs {comptaVarRevenus.color}">{comptaVarRevenus.text}</span>{/if}
								</td>
								<td class="pt-3 text-right font-bold text-slate-900 dark:text-slate-100">
									{formatEur(comptaData.totaux?.charges)}
									{#if comptaVarCharges}<span class="ml-1 text-xs {comptaVarCharges.color}">{comptaVarCharges.text}</span>{/if}
								</td>
								<td class="pt-3 text-right font-bold text-slate-900 dark:text-slate-100">
									{formatEur(comptaData.totaux?.evenements_deductibles)}
								</td>
								<td class="pt-3 text-right font-bold {comptaData.totaux?.resultat >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}">
									{formatEur(comptaData.totaux?.resultat)}
									{#if comptaVarResultat}<span class="ml-1 text-xs {comptaVarResultat.color}">{comptaVarResultat.text}</span>{/if}
								</td>
							</tr>
						</tfoot>
					</table>
				</div>
			{:else}
				<p class="mt-4 text-sm text-slate-500 dark:text-slate-400">Aucune donnée comptable pour {comptaYear}.</p>
			{/if}
		{:else}
			<!-- Vue mensuelle (graphique barres) -->
			{#if mensuelLoading}
				<div class="mt-4 flex items-center justify-center py-8">
					<Loader2 class="h-5 w-5 animate-spin text-slate-400" />
				</div>
			{:else if mensuelError}
				<p class="mt-4 text-sm text-rose-600 dark:text-rose-400">{mensuelError}</p>
			{:else if mensuelData.length > 0}
				<!-- Légende -->
				<div class="mt-4 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
					<span class="flex items-center gap-1.5">
						<span class="inline-block h-2.5 w-2.5 rounded-sm bg-emerald-500"></span>
						Revenus
					</span>
					<span class="flex items-center gap-1.5">
						<span class="inline-block h-2.5 w-2.5 rounded-sm bg-rose-400"></span>
						Charges
					</span>
				</div>
				<!-- Bar chart -->
				<div class="mt-3 flex items-end gap-1 overflow-x-auto pb-1" style="height: 160px;" role="img" aria-label="Graphique revenus vs charges mensuels {comptaYear}">
					{#each mensuelData as month, i}
						{@const revPct = mensuelMax > 0 ? (month.revenus / mensuelMax) * 100 : 0}
						{@const chgPct = mensuelMax > 0 ? (month.charges / mensuelMax) * 100 : 0}
						<div class="group relative flex flex-1 flex-col items-center gap-0.5" style="min-width: 40px;">
							<!-- Bars container -->
							<div class="flex w-full items-end justify-center gap-0.5" style="height: 130px;">
								<div
									class="w-3 rounded-t bg-emerald-500 transition-all duration-300 sm:w-4"
									style="height: {revPct}%; min-height: {month.revenus > 0 ? '4px' : '0px'};"
									title="Revenus {MOIS_LABELS[i]} : {formatEur(month.revenus)}"
								></div>
								<div
									class="w-3 rounded-t bg-rose-400 transition-all duration-300 sm:w-4"
									style="height: {chgPct}%; min-height: {month.charges > 0 ? '4px' : '0px'};"
									title="Charges {MOIS_LABELS[i]} : {formatEur(month.charges)}"
								></div>
							</div>
							<!-- Month label -->
							<span class="mt-1 text-[10px] font-medium text-slate-400 dark:text-slate-500">{MOIS_LABELS[i]}</span>
							<!-- Tooltip on hover -->
							<div class="pointer-events-none absolute -top-14 left-1/2 z-10 hidden -translate-x-1/2 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs shadow-lg group-hover:block dark:border-slate-700 dark:bg-slate-900">
								<p class="whitespace-nowrap font-medium text-slate-700 dark:text-slate-200">{MOIS_LABELS[i]} {comptaYear}</p>
								<p class="whitespace-nowrap text-emerald-600 dark:text-emerald-400">{formatEur(month.revenus)}</p>
								<p class="whitespace-nowrap text-rose-500 dark:text-rose-400">{formatEur(month.charges)}</p>
							</div>
						</div>
					{/each}
				</div>
				<!-- Monthly totals summary -->
				{@const totalRevMensuel = mensuelData.reduce((s, m) => s + m.revenus, 0)}
				{@const totalChgMensuel = mensuelData.reduce((s, m) => s + m.charges, 0)}
				<div class="mt-3 flex flex-wrap items-center gap-4 border-t border-slate-100 pt-3 text-sm dark:border-slate-800">
					<span class="text-slate-500 dark:text-slate-400">
						Total revenus : <span class="font-semibold text-emerald-700 dark:text-emerald-300">{formatEur(totalRevMensuel)}</span>
					</span>
					<span class="text-slate-500 dark:text-slate-400">
						Total charges : <span class="font-semibold text-rose-700 dark:text-rose-300">{formatEur(totalChgMensuel)}</span>
					</span>
					<span class="text-slate-500 dark:text-slate-400">
						Résultat : <span class="font-semibold {totalRevMensuel - totalChgMensuel >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}">{formatEur(totalRevMensuel - totalChgMensuel)}</span>
					</span>
				</div>
			{:else}
				<p class="mt-4 text-sm text-slate-500 dark:text-slate-400">Aucune donnée mensuelle pour {comptaYear}.</p>
			{/if}
		{/if}
	</div>

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
