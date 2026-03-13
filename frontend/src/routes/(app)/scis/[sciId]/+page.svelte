<script lang="ts">
	import { getContext } from 'svelte';
	import { Building2, Users, FileText, MapPin, FolderOpen, Download, Wallet, TrendingUp, Receipt, AlertTriangle, CalendarDays, Clock, CheckCircle2, Pencil, Trash2, Loader2 } from 'lucide-svelte';
	import type { SCIDetail } from '$lib/api';
	import { fetchSciBiensList, exportBiensCsv, exportLoyersCsv, deleteSci } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import { Button } from '$lib/components/ui/button';
	import { addToast } from '$lib/components/ui/toast';
	import { goto } from '$app/navigation';

	const sci = getContext<SCIDetail>('sci');
	const sciId = getContext<string>('sciId');
	const userRole = getContext<string>('userRole');

	let biensCount = $state(sci.biens_count ?? sci.biens?.length ?? 0);
	let loadingBiens = $state(false);
	let exportingBiens = $state(false);
	let exportingLoyers = $state(false);

	// Delete SCI state
	let showDeleteConfirm = $state(false);
	let deletingSci = $state(false);

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

	const allDeadlines: FiscalEvent[] = [
		...(regime === 'IR' ? [
			{ key: 'declaration_2072', label: 'Déclaration 2072', date: new Date(currentYear, 4, 20), regime: 'IR', description: 'Déclaration des résultats de la SCI à l\'IR' },
			{ key: 'declaration_2044', label: 'Déclaration 2044', date: new Date(currentYear, 4, 31), regime: 'IR', description: 'Déclaration individuelle des revenus fonciers (chaque associé)' },
		] : []),
		...(regime === 'IS' ? [
			{ key: 'liasse_fiscale_is', label: 'Liasse fiscale IS', date: new Date(currentYear, 2, 31), regime: 'IS', description: 'Liasse fiscale pour SCI à l\'IS (3 mois post-clôture)' },
		] : []),
		{ key: 'ag_annuelle', label: 'AG annuelle', date: new Date(currentYear, 5, 30), regime: null, description: 'Assemblée générale obligatoire (6 mois post-clôture)' },
		{ key: 'taxe_fonciere', label: 'Taxe foncière', date: new Date(currentYear, 9, 15), regime: null, description: 'Paiement de la taxe foncière' },
		{ key: 'cfe', label: 'CFE', date: new Date(currentYear, 11, 15), regime: null, description: 'Cotisation Foncière des Entreprises' },
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

	async function handleExportBiens() {
		exportingBiens = true;
		try {
			const blob = await exportBiensCsv(sciId); // TODO: backend needs to support sci_id filter for scoped export
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
			const blob = await exportLoyersCsv(sciId); // TODO: backend needs to support sci_id filter for scoped export
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

<svelte:head><title>{sci.nom} | GererSCI</title></svelte:head>

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
				{#if isGerant}
					<a
						href="/scis/{sciId}/settings"
						class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
					>
						<Pencil class="h-3.5 w-3.5" />
						Modifier
					</a>
					<button
						onclick={() => { showDeleteConfirm = true; }}
						class="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-sm font-medium text-rose-600 transition-colors hover:bg-rose-50 dark:border-rose-800 dark:bg-slate-900 dark:text-rose-400 dark:hover:bg-rose-950/30"
						title="Supprimer la SCI"
					>
						<Trash2 class="h-3.5 w-3.5" />
						Supprimer
					</button>
				{/if}
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
					<a href="/scis/{sciId}/biens" class="mt-2 inline-flex text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400">
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
				<div class="flex items-center gap-3 rounded-xl {status.bg} px-4 py-3">
					<div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-white/80 dark:bg-slate-800/80">
						{#if event.daysUntil < 0}
							<CheckCircle2 class="h-4 w-4 {status.iconColor}" />
						{:else}
							<Clock class="h-4 w-4 {status.iconColor}" />
						{/if}
					</div>
					<div class="min-w-0 flex-1">
						<div class="flex items-center justify-between gap-2">
							<p class="text-sm font-medium {event.daysUntil < 0 ? 'text-slate-400 line-through dark:text-slate-500' : 'text-slate-900 dark:text-slate-100'}">
								{event.label}
							</p>
							<span class="flex-shrink-0 text-xs font-semibold {status.color}">
								{status.label}
							</span>
						</div>
						<p class="text-xs {event.daysUntil < 0 ? 'text-slate-400 dark:text-slate-500' : 'text-slate-500 dark:text-slate-400'}">
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
			</div>
		</div>

		<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
			<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Exports</h2>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">Télécharger les données de cette SCI au format CSV.</p>
			<div class="mt-4 grid gap-3">
				<Button onclick={handleExportBiens} disabled={exportingBiens} variant="outline" class="justify-start">
					<Download class="mr-2 h-4 w-4" />
					{exportingBiens ? 'Export en cours...' : 'Exporter les biens (CSV)'}
				</Button>
				<Button onclick={handleExportLoyers} disabled={exportingLoyers} variant="outline" class="justify-start">
					<Download class="mr-2 h-4 w-4" />
					{exportingLoyers ? 'Export en cours...' : 'Exporter les loyers (CSV)'}
				</Button>
			</div>
		</div>
	</div>

	<!-- Delete SCI Confirmation Modal -->
	{#if showDeleteConfirm}
		<div
			role="alertdialog"
			aria-modal="true"
			aria-labelledby="delete-sci-title"
			aria-describedby="delete-sci-desc"
			class="fixed inset-0 z-50 flex items-center justify-center p-4"
		>
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick={() => { if (!deletingSci) showDeleteConfirm = false; }}></div>
			<div class="relative w-full max-w-[420px] rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-900">
				<div class="flex items-start gap-3">
					<div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-rose-100 dark:bg-rose-900/40">
						<Trash2 class="h-5 w-5 text-rose-600 dark:text-rose-400" />
					</div>
					<div>
						<h2 id="delete-sci-title" class="text-base font-semibold text-slate-900 dark:text-slate-100">Supprimer {sci.nom} ?</h2>
						<p id="delete-sci-desc" class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							Cette action est irréversible. Tous les biens, baux, loyers et documents associés seront supprimés.
						</p>
					</div>
				</div>
				<div class="mt-5 flex items-center justify-end gap-2">
					<button onclick={() => { showDeleteConfirm = false; }} disabled={deletingSci}
						class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800">
						Annuler
					</button>
					<button onclick={handleDeleteSci} disabled={deletingSci}
						class="inline-flex items-center gap-2 rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50">
						{#if deletingSci}<Loader2 class="h-4 w-4 animate-spin" />{/if}
						Supprimer définitivement
					</button>
				</div>
			</div>
		</div>
	{/if}
</section>
