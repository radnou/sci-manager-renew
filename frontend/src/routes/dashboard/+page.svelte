<script lang="ts">
	import { onMount } from 'svelte';
	import { HandCoins } from 'lucide-svelte';
	import {
		fetchSciDetail,
		fetchBiens,
		fetchLoyers,
		fetchScis,
		type Bien,
		type Loyer,
		type SCIDetail,
		type SCIOverview
	} from '$lib/api';
	import BienTable from '$lib/components/BienTable.svelte';
	import LoyerTable from '$lib/components/LoyerTable.svelte';
	import QuitusGenerator from '$lib/components/QuitusGenerator.svelte';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { calculateBienMetrics } from '$lib/high-value/biens';
	import { calculateLoyerMetrics } from '$lib/high-value/loyers';
	import { calculatePortfolioMetrics, calculateSciScopeMetrics } from '$lib/high-value/portfolio';
	import { formatEur, formatPercent } from '$lib/high-value/formatters';
	import { formatApiErrorMessage, mapAssociateRoleLabel, mapChargeTypeLabel } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	import PortfolioKPIStrip from '$lib/components/dashboard/PortfolioKPIStrip.svelte';
	import SCIGrid from '$lib/components/dashboard/SCIGrid.svelte';
	import PortfolioSummary from '$lib/components/dashboard/PortfolioSummary.svelte';
	import CockpitHeader from '$lib/components/dashboard/CockpitHeader.svelte';
	import AssociatesPanel from '$lib/components/dashboard/AssociatesPanel.svelte';
	import SCIIdentityCard from '$lib/components/dashboard/SCIIdentityCard.svelte';
	import ChargesFiscalPanel from '$lib/components/dashboard/ChargesFiscalPanel.svelte';
	import ScopedKPIStrip from '$lib/components/dashboard/ScopedKPIStrip.svelte';
	import OperatorRituals from '$lib/components/dashboard/OperatorRituals.svelte';
	import CollectionChart from '$lib/components/charts/CollectionChart.svelte';
	import RentTrendChart from '$lib/components/charts/RentTrendChart.svelte';
	import PortfolioAllocationChart from '$lib/components/charts/PortfolioAllocationChart.svelte';
	import AlertBanner from '$lib/components/AlertBanner.svelte';
	import OnboardingWizard from '$lib/components/OnboardingWizard.svelte';

	let biens: Bien[] = [];
	let loyers: Loyer[] = [];
	let scis: SCIOverview[] = [];
	let activeSciDetail: SCIDetail | null = null;
	let activeSciId = '';
	let loading = true;
	let detailLoading = true;
	let errorMessage = '';
	let detailErrorMessage = '';
	let detailLoadedFor = '';
	let detailRequestVersion = 0;

	const emptyBienMetrics = calculateBienMetrics([]);
	const emptyLoyerMetrics = calculateLoyerMetrics([]);

	$: sciSnapshots = scis.map((sci) => ({
		sci,
		...calculateSciScopeMetrics(sci.id, biens, loyers)
	}));
	$: resolvedActiveSciId =
		activeSciId && scis.some((sci) => String(sci.id) === activeSciId)
			? activeSciId
			: String(scis[0]?.id || '');
	$: activeSnapshot =
		sciSnapshots.find((snapshot) => String(snapshot.sci.id) === resolvedActiveSciId) ?? null;
	$: activeSci = activeSnapshot?.sci ?? null;
	$: activeSciProfile =
		activeSciDetail && String(activeSciDetail.id || '') === resolvedActiveSciId
			? activeSciDetail
			: activeSci;
	$: scopedBiens = activeSnapshot?.biens ?? [];
	$: scopedLoyers = activeSnapshot?.loyers ?? [];
	$: bienMetrics = activeSnapshot?.bienMetrics ?? emptyBienMetrics;
	$: loyerMetrics = activeSnapshot?.loyerMetrics ?? emptyLoyerMetrics;
	$: portfolioMetrics = calculatePortfolioMetrics(scis, biens, loyers);
	$: collectionRate = loyerMetrics.collectionRate;
	$: monthlyPropertyCharges = scopedBiens.reduce((sum, bien) => sum + (bien.charges ?? 0), 0);
	$: avgAssociateShare =
		activeSciProfile && activeSciProfile.associes_count && activeSciProfile.associes_count > 0
			? 100 / activeSciProfile.associes_count
			: 0;
	$: associateSummary = activeSciDetail?.associes ?? activeSci?.associes ?? [];
	$: recentLoyerFeed = [
		...(activeSciDetail?.recent_loyers?.length ? activeSciDetail.recent_loyers : scopedLoyers)
	].sort((left, right) => toTimestamp(right.date_loyer) - toTimestamp(left.date_loyer));
	$: latestLoyer = recentLoyerFeed[0] ?? null;
	$: recentChargeFeed = [...(activeSciDetail?.recent_charges ?? [])].sort(
		(left, right) => toTimestamp(right.date_paiement) - toTimestamp(left.date_paiement)
	);
	$: latestCharge = recentChargeFeed[0] ?? null;
	$: fiscalTimeline = [...(activeSciDetail?.fiscalite ?? [])].sort(
		(left, right) => (right.annee ?? 0) - (left.annee ?? 0)
	);
	$: latestFiscalYear = fiscalTimeline[0] ?? null;

	$: priorities = [
		{
			title: scopedBiens.length === 0 ? 'Structurer le patrimoine' : 'Mettre à jour le portefeuille',
			description: scopedBiens.length === 0
				? 'Aucun bien n\'est encore rattaché à la SCI active. Commence par documenter le premier actif.'
				: `${scopedBiens.length} biens rattachés à la SCI active. Vérifie les loyers et charges du mois.`,
			tone: scopedBiens.length === 0 ? 'warning' : 'default'
		},
		{
			title: loyerMetrics.lateCount > 0 ? 'Traiter les retards' : loyerMetrics.totalOutstanding > 0 ? 'Encaissements à sécuriser' : 'Suivi des encaissements sous contrôle',
			description: loyerMetrics.lateCount > 0
				? `${loyerMetrics.lateCount} loyer(s) en retard nécessitent une relance ou un arbitrage.`
				: loyerMetrics.totalOutstanding > 0
					? `${loyerMetrics.totalOutstandingLabel} restent en attente d'encaissement sur la SCI active.`
					: 'Tous les flux saisis sont encaissés. Tu peux préparer les quittances et la revue mensuelle.',
			tone: loyerMetrics.lateCount > 0 ? 'danger' : loyerMetrics.totalOutstanding > 0 ? 'warning' : 'success'
		},
		{
			title: associateSummary.length > 1 ? 'Coordonner les associés' : 'Gouvernance simple',
			description: associateSummary.length > 1
				? `${associateSummary.length} associés sont impliqués. Prépare un point de gouvernance avant les arbitrages.`
				: 'La SCI est portée par un seul associé référent. Les validations sont fluides.',
			tone: 'accent'
		}
	];

	$: commandTracks = [
		{
			id: 'dashboard-governance',
			label: 'Gouvernance',
			summary: associateSummary.length > 0 ? `${associateSummary.length} associé(s) documenté(s)` : 'Associés à documenter',
			detail: activeSciProfile?.user_role ? `${mapAssociateRoleLabel(activeSciProfile.user_role)} connecté` : 'Rôle utilisateur à confirmer'
		},
		{
			id: 'dashboard-patrimoine',
			label: 'Patrimoine',
			summary: `${activeSciDetail?.biens_count ?? scopedBiens.length} bien(s) actifs`,
			detail: `Loyer cible ${formatEur(activeSciDetail?.total_monthly_rent ?? bienMetrics.totalMonthlyRent)}`
		},
		{
			id: 'dashboard-execution',
			label: 'Encaissements',
			summary: `Recouvrement ${formatPercent(collectionRate, '0%')}`,
			detail: loyerMetrics.lateCount > 0
				? `${loyerMetrics.lateCount} retard(s) à traiter`
				: loyerMetrics.totalOutstanding > 0
					? `${loyerMetrics.totalOutstandingLabel} à sécuriser`
					: 'Aucun retard détecté'
		},
		{
			id: 'dashboard-documents',
			label: 'Documents',
			summary: latestFiscalYear ? `Exercice ${latestFiscalYear.annee} consolidé` : 'Clôture fiscale à préparer',
			detail: scopedLoyers.length > 0
				? `${scopedLoyers.length} loyer(s) saisi(s), quittances générables`
				: 'Aucun loyer saisi pour produire une quittance'
		}
	];

	$: if (resolvedActiveSciId) setStoredActiveSciId(resolvedActiveSciId);

	$: if (!resolvedActiveSciId) {
		activeSciDetail = null;
		detailLoading = false;
		detailErrorMessage = '';
		detailLoadedFor = '';
	} else if (detailLoadedFor !== resolvedActiveSciId) {
		detailLoadedFor = resolvedActiveSciId;
		void loadSciDetail(resolvedActiveSciId);
	}

	function toTimestamp(value: string | null | undefined) {
		if (!value) return 0;
		const parsed = Date.parse(value);
		return Number.isNaN(parsed) ? 0 : parsed;
	}

	onMount(loadOverview);

	async function loadOverview() {
		loading = true;
		errorMessage = '';
		try {
			const [nextScis, nextBiens, nextLoyers] = await Promise.all([fetchScis(), fetchBiens(), fetchLoyers()]);
			scis = Array.isArray(nextScis) ? nextScis : [];
			biens = Array.isArray(nextBiens) ? nextBiens : [];
			loyers = Array.isArray(nextLoyers) ? nextLoyers : [];
			const storedActiveSciId = getStoredActiveSciId();
			const fallbackSci = nextScis[0];
			activeSciId =
				(storedActiveSciId && nextScis.some((sci) => String(sci.id) === storedActiveSciId) && storedActiveSciId) ||
				String(fallbackSci?.id || '');
			if (!nextScis.length) {
				activeSciDetail = null;
				detailLoadedFor = '';
				detailLoading = false;
				detailErrorMessage = '';
			}
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de charger le cockpit SCI.');
		} finally {
			loading = false;
		}
	}

	async function loadSciDetail(sciId: string) {
		const requestVersion = ++detailRequestVersion;
		detailLoading = true;
		detailErrorMessage = '';
		activeSciDetail = null;
		try {
			const nextDetail = await fetchSciDetail(sciId);
			if (requestVersion !== detailRequestVersion) return;
			activeSciDetail = nextDetail;
		} catch (error) {
			if (requestVersion !== detailRequestVersion) return;
			activeSciDetail = null;
			detailErrorMessage = formatApiErrorMessage(error, 'Impossible de charger le dashboard spécifique de la SCI active.');
		} finally {
			if (requestVersion !== detailRequestVersion) return;
			detailLoading = false;
		}
	}

	function handleSciSelect(id: string) {
		activeSciId = id;
		errorMessage = '';
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Pilotage SCI • Cockpit exécutif</p>
		<h1 class="sci-page-title">Dashboard de portefeuille</h1>
		<p class="sci-page-subtitle">
			Vue portefeuille de toutes les SCI accessibles. Sélectionnez une SCI active pour la lecture opérationnelle.
		</p>
	</header>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	{#if !loading && loyerMetrics.lateCount > 0}
		<div class="mb-4">
			<AlertBanner
				type="danger"
				message="{loyerMetrics.lateCount} loyer(s) en retard nécessitent une action immédiate."
				href="#dashboard-execution"
			/>
		</div>
	{/if}

	{#if !loading}
		<div class="mb-6">
			<OnboardingWizard
				hasSci={scis.length > 0}
				hasBien={biens.length > 0}
				hasLoyer={loyers.length > 0}
				hasQuittance={loyers.some((l) => l.quitus_genere)}
			/>
		</div>
	{/if}

	<PortfolioKPIStrip metrics={portfolioMetrics} {loading} />

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.55fr_1fr]">
		<SCIGrid snapshots={sciSnapshots} activeSciId={resolvedActiveSciId} {loading} onSelect={handleSciSelect} />
		<PortfolioSummary metrics={portfolioMetrics} />
	</div>

	{#if !loading && loyers.length > 0}
		<div class="mt-6 grid gap-6 lg:grid-cols-3">
			<CollectionChart loyers={scopedLoyers} />
			<RentTrendChart loyers={scopedLoyers} />
			<PortfolioAllocationChart {biens} {scis} />
		</div>
	{/if}

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.8fr_1fr]">
		<div class="xl:col-span-2">
			<div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
				<div>
					<p class="sci-eyebrow">SCI active • Dashboard spécifique</p>
					<h2 class="text-2xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
						Cockpit d'exécution par cas d'usage
					</h2>
					<p class="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
						Le portefeuille reste en haut. Ici, la SCI active est organisée par cas d'usage opérateur.
					</p>
				</div>
			</div>
			{#if detailErrorMessage}
				<p class="sci-inline-alert sci-inline-alert-error">{detailErrorMessage}</p>
			{/if}
		</div>

		<CockpitHeader
			{activeSciProfile}
			{scis}
			activeSciId={resolvedActiveSciId}
			{collectionRate}
			{avgAssociateShare}
			{loyerMetrics}
			{commandTracks}
			{priorities}
			onSciChange={handleSciSelect}
		/>
		<AssociatesPanel associates={associateSummary} />
	</div>

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.25fr_1fr]">
		<SCIIdentityCard {activeSciProfile} {activeSciDetail} {scopedBiens} {bienMetrics} {detailLoading} />
		<ChargesFiscalPanel
			totalRecordedCharges={activeSciDetail?.total_recorded_charges}
			chargesCount={activeSciDetail?.charges_count ?? 0}
			recentCharges={recentChargeFeed}
			{latestFiscalYear}
			{detailLoading}
		/>
	</div>

	<div class="mt-6">
		<ScopedKPIStrip {bienMetrics} {loyerMetrics} {collectionRate} {loading} />
	</div>

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.8fr_1fr]">
		<div class="space-y-6">
			<div id="dashboard-patrimoine" class="scroll-mt-28">
				<BienTable
					biens={scopedBiens.slice(0, 6)}
					{loading}
					title="Patrimoine piloté"
					description="Vue consolidée des biens de la SCI active."
				/>
			</div>

			<Card id="dashboard-execution" class="sci-section-card scroll-mt-28">
				<CardHeader>
					<CardTitle class="flex items-center gap-2 text-lg">
						<HandCoins class="h-5 w-5 text-emerald-600" />
						Mouvements et alertes
					</CardTitle>
					<CardDescription>Trésorerie et production des quittances.</CardDescription>
				</CardHeader>
				<CardContent>
					<LoyerTable
						loyers={scopedLoyers.slice(0, 8)}
						biens={scopedBiens}
						{loading}
						title="Journal de la SCI active"
						description="Historique opérationnel."
					/>
				</CardContent>
			</Card>
		</div>

		<div class="space-y-6">
			<div id="dashboard-documents" class="scroll-mt-28">
				<QuitusGenerator
					loyers={scopedLoyers}
					biens={scopedBiens}
					sciName={activeSciProfile?.nom || activeSci?.nom || ''}
				/>
			</div>
			<OperatorRituals
				{latestLoyer}
				{scopedLoyers}
				{monthlyPropertyCharges}
				{latestFiscalYear}
				{latestCharge}
			/>
		</div>
	</div>
</section>
