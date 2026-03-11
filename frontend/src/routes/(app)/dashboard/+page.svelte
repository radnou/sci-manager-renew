<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { HandCoins, Building2, FileText, Users, BarChart3 } from 'lucide-svelte';
	import {
		fetchSciDetail,
		fetchBiens,
		fetchLoyers,
		fetchScis,
		updateLoyer,
		type Bien,
		type Loyer,
		type SCIDetail,
		type SCIOverview
	} from '$lib/api';
	import BienTable from '$lib/components/BienTable.svelte';
	import LoyerTable from '$lib/components/LoyerTable.svelte';
	import QuitusGenerator from '$lib/components/QuitusGenerator.svelte';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { calculateBienMetrics } from '$lib/high-value/biens';
	import { calculateLoyerMetrics } from '$lib/high-value/loyers';
	import { calculatePortfolioMetrics, calculateSciScopeMetrics } from '$lib/high-value/portfolio';
	import { formatEur, formatPercent } from '$lib/high-value/formatters';
	import {
		formatApiErrorMessage,
		mapAssociateRoleLabel,
		mapChargeTypeLabel
	} from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	import PortfolioKPIStrip from '$lib/components/dashboard/PortfolioKPIStrip.svelte';
	import SCIGrid from '$lib/components/dashboard/SCIGrid.svelte';
	import PortfolioSummary from '$lib/components/dashboard/PortfolioSummary.svelte';
	import AssociatesPanel from '$lib/components/dashboard/AssociatesPanel.svelte';
	import SCIIdentityCard from '$lib/components/dashboard/SCIIdentityCard.svelte';
	import ChargesFiscalPanel from '$lib/components/dashboard/ChargesFiscalPanel.svelte';
	import ScopedKPIStrip from '$lib/components/dashboard/ScopedKPIStrip.svelte';
	import CollectionChart from '$lib/components/charts/CollectionChart.svelte';
	import RentTrendChart from '$lib/components/charts/RentTrendChart.svelte';
	import PortfolioAllocationChart from '$lib/components/charts/PortfolioAllocationChart.svelte';
	import AlertBanner from '$lib/components/AlertBanner.svelte';
	import OnboardingWizard from '$lib/components/OnboardingWizard.svelte';

	let biens = $state<Bien[]>([]);
	let loyers = $state<Loyer[]>([]);
	let scis = $state<SCIOverview[]>([]);
	let activeSciDetail = $state<SCIDetail | null>(null);
	let activeSciId = $state('');
	let loading = $state(true);
	let detailLoading = $state(true);
	let errorMessage = $state('');
	let detailErrorMessage = $state('');
	let detailLoadedFor = $state('');
	let detailRequestVersion = 0;
	let activeTab = $state<'flux' | 'patrimoine' | 'documents' | 'gouvernance' | 'analytique'>(
		'flux'
	);

	const emptyBienMetrics = calculateBienMetrics([]);
	const emptyLoyerMetrics = calculateLoyerMetrics([]);

	const sciSnapshots = $derived(
		scis.map((sci) => ({
			sci,
			...calculateSciScopeMetrics(sci.id, biens, loyers)
		}))
	);
	const resolvedActiveSciId = $derived(
		activeSciId && scis.some((sci) => String(sci.id) === activeSciId)
			? activeSciId
			: String(scis[0]?.id || '')
	);
	const activeSnapshot = $derived(
		sciSnapshots.find((snapshot) => String(snapshot.sci.id) === resolvedActiveSciId) ?? null
	);
	const activeSci = $derived(activeSnapshot?.sci ?? null);
	const activeSciProfile = $derived(
		activeSciDetail && String(activeSciDetail.id || '') === resolvedActiveSciId
			? activeSciDetail
			: activeSci
	);
	const scopedBiens = $derived(activeSnapshot?.biens ?? []);
	const scopedLoyers = $derived(activeSnapshot?.loyers ?? []);
	const bienMetrics = $derived(activeSnapshot?.bienMetrics ?? emptyBienMetrics);
	const loyerMetrics = $derived(activeSnapshot?.loyerMetrics ?? emptyLoyerMetrics);
	const portfolioMetrics = $derived(calculatePortfolioMetrics(scis, biens, loyers));
	const collectionRate = $derived(loyerMetrics.collectionRate);
	const monthlyPropertyCharges = $derived(
		scopedBiens.reduce((sum, bien) => sum + (bien.charges ?? 0), 0)
	);
	const associateSummary = $derived(activeSciDetail?.associes ?? activeSci?.associes ?? []);
	const recentLoyerFeed = $derived(
		[
			...(activeSciDetail?.recent_loyers?.length ? activeSciDetail.recent_loyers : scopedLoyers)
		].sort((left, right) => toTimestamp(right.date_loyer) - toTimestamp(left.date_loyer))
	);
	const recentChargeFeed = $derived(
		[...(activeSciDetail?.recent_charges ?? [])].sort(
			(left, right) => toTimestamp(right.date_paiement) - toTimestamp(left.date_paiement)
		)
	);
	const latestFiscalYear = $derived(
		[...(activeSciDetail?.fiscalite ?? [])].sort(
			(left, right) => (right.annee ?? 0) - (left.annee ?? 0)
		)[0] ?? null
	);

	const lateLoyers = $derived(
		scopedLoyers.filter((l) => l.statut === 'en_retard' || l.statut === 'retard')
	);
	const pendingLoyers = $derived(scopedLoyers.filter((l) => l.statut === 'en_attente'));

	$effect(() => {
		if (resolvedActiveSciId) setStoredActiveSciId(resolvedActiveSciId);
	});

	$effect(() => {
		if (!resolvedActiveSciId) {
			activeSciDetail = null;
			detailLoading = false;
			detailErrorMessage = '';
			detailLoadedFor = '';
		} else if (detailLoadedFor !== resolvedActiveSciId) {
			detailLoadedFor = resolvedActiveSciId;
			void loadSciDetail(resolvedActiveSciId);
		}
	});

	const tabs = [
		{ id: 'flux' as const, label: 'Flux', icon: HandCoins },
		{ id: 'patrimoine' as const, label: 'Patrimoine', icon: Building2 },
		{ id: 'documents' as const, label: 'Documents', icon: FileText },
		{ id: 'gouvernance' as const, label: 'Gouvernance', icon: Users },
		{ id: 'analytique' as const, label: 'Analytique', icon: BarChart3 }
	];

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
			const [nextScis, nextBiens, nextLoyers] = await Promise.all([
				fetchScis(),
				fetchBiens(),
				fetchLoyers()
			]);
			scis = Array.isArray(nextScis) ? nextScis : [];
			biens = Array.isArray(nextBiens) ? nextBiens : [];
			loyers = Array.isArray(nextLoyers) ? nextLoyers : [];
			const storedActiveSciId = getStoredActiveSciId();
			const fallbackSci = nextScis[0];
			activeSciId =
				(storedActiveSciId &&
					nextScis.some((sci) => String(sci.id) === storedActiveSciId) &&
					storedActiveSciId) ||
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
			detailErrorMessage = formatApiErrorMessage(
				error,
				'Impossible de charger le détail de la SCI.'
			);
		} finally {
			if (requestVersion !== detailRequestVersion) return;
			detailLoading = false;
		}
	}

	function handleSciSelect(id: string) {
		activeSciId = id;
		errorMessage = '';
	}

	async function markLoyerPaid(loyerId: string | number) {
		try {
			await updateLoyer(loyerId, { statut: 'paye' });
			await loadOverview();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de marquer le loyer comme payé.');
		}
	}
</script>

<section class="sci-page-shell">
	<!-- ═══════════════════════════════════════════════════════════ -->
	<!-- ZONE 1 — Alertes & Actions                                  -->
	<!-- ═══════════════════════════════════════════════════════════ -->
	<header class="sci-page-header">
		<p class="sci-eyebrow">Pilotage SCI</p>
		<h1 class="sci-page-title">Dashboard</h1>
	</header>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	{#if !loading}
		<div class="space-y-3">
			<OnboardingWizard
				hasSci={scis.length > 0}
				hasBien={biens.length > 0}
				hasLoyer={loyers.length > 0}
				hasQuittance={loyers.some((l) => l.quitus_genere)}
			/>

			{#if lateLoyers.length > 0}
				<AlertBanner
					type="danger"
					message="{lateLoyers.length} loyer(s) en retard nécessitent une action."
					actions={[
						{
							label: 'Traiter les retards',
							onclick: () => {
								activeTab = 'flux';
							}
						},
						...(lateLoyers.length === 1
							? [{ label: 'Marquer payé', onclick: () => markLoyerPaid(lateLoyers[0].id!) }]
							: [])
					]}
				/>
			{/if}

			{#if scopedBiens.length === 0 && scis.length > 0}
				<AlertBanner
					type="warning"
					message="Aucun bien rattaché à la SCI active. Documentez votre premier actif."
					actions={[{ label: 'Ajouter un bien', onclick: () => goto('/biens') }]}
				/>
			{/if}

			{#if pendingLoyers.length > 3}
				<AlertBanner
					type="info"
					message="{pendingLoyers.length} loyers en attente d'encaissement."
					actions={[
						{
							label: 'Voir les loyers',
							onclick: () => {
								activeTab = 'flux';
							}
						}
					]}
				/>
			{/if}
		</div>
	{/if}

	<!-- ═══════════════════════════════════════════════════════════ -->
	<!-- ZONE 2 — KPIs Situation                                      -->
	<!-- ═══════════════════════════════════════════════════════════ -->
	<div class="mt-6">
		<PortfolioKPIStrip metrics={portfolioMetrics} {loading} />
	</div>

	{#if scis.length > 1}
		<div class="mt-6 grid gap-6 xl:grid-cols-[1.55fr_1fr]">
			<SCIGrid
				snapshots={sciSnapshots}
				activeSciId={resolvedActiveSciId}
				{loading}
				onSelect={handleSciSelect}
			/>
			<PortfolioSummary metrics={portfolioMetrics} />
		</div>
	{/if}

	{#if scis.length > 1}
		<div class="mt-4 flex items-center gap-3">
			<span class="text-xs font-semibold tracking-wider text-slate-500 uppercase">SCI active</span>
			<select
				class="sci-select max-w-xs text-sm"
				value={resolvedActiveSciId}
				onchange={(e) => handleSciSelect((e.target as HTMLSelectElement).value)}
				aria-label="SCI active"
			>
				{#each scis as sci (String(sci.id))}
					<option value={String(sci.id)}>{sci.nom}</option>
				{/each}
			</select>
		</div>
	{/if}

	<div class="mt-4">
		<ScopedKPIStrip {bienMetrics} {loyerMetrics} {collectionRate} {loading} />
	</div>

	<!-- ═══════════════════════════════════════════════════════════ -->
	<!-- ZONE 3 — Onglets détail                                      -->
	<!-- ═══════════════════════════════════════════════════════════ -->
	<div class="mt-8">
		{#if detailErrorMessage}
			<p class="sci-inline-alert sci-inline-alert-error mb-4">{detailErrorMessage}</p>
		{/if}

		<div
			role="tablist"
			class="flex gap-1 overflow-x-auto border-b border-slate-200 dark:border-slate-800"
		>
			{#each tabs as tab (tab.id)}
				<button
					type="button"
					role="tab"
					aria-selected={activeTab === tab.id}
					class="flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors {activeTab ===
					tab.id
						? 'border-slate-900 text-slate-900 dark:border-slate-100 dark:text-slate-100'
						: 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700 dark:text-slate-400 dark:hover:border-slate-600 dark:hover:text-slate-200'}"
					onclick={() => (activeTab = tab.id)}
				>
					<tab.icon class="h-4 w-4" />
					{tab.label}
					{#if tab.id === 'flux' && lateLoyers.length > 0}
						<span
							class="rounded-full bg-rose-100 px-1.5 py-0.5 text-[0.65rem] font-bold text-rose-700 dark:bg-rose-900 dark:text-rose-200"
							>{lateLoyers.length}</span
						>
					{/if}
				</button>
			{/each}
		</div>

		<div class="mt-6" role="tabpanel">
			<!-- ─── Tab: Flux ─── -->
			{#if activeTab === 'flux'}
				<div class="space-y-6">
					{#if lateLoyers.length > 0}
						<Card class="border-rose-200 dark:border-rose-800">
							<CardHeader>
								<CardTitle class="text-lg text-rose-700 dark:text-rose-300"
									>Retards à traiter</CardTitle
								>
								<CardDescription
									>{lateLoyers.length} loyer(s) en retard nécessitent une action immédiate.</CardDescription
								>
							</CardHeader>
							<CardContent>
								<div class="space-y-2">
									{#each lateLoyers as loyer}
										{@const bien = scopedBiens.find((b) => String(b.id) === String(loyer.id_bien))}
										<div
											class="flex items-center justify-between rounded-lg border border-rose-100 bg-rose-50/50 px-4 py-3 dark:border-rose-900 dark:bg-rose-950/20"
										>
											<div>
												<p class="text-sm font-medium text-slate-900 dark:text-slate-100">
													{bien?.adresse ?? 'Bien inconnu'} — {formatEur(loyer.montant)}
												</p>
												<p class="text-xs text-slate-500">{loyer.date_loyer}</p>
											</div>
											<div class="flex gap-2">
												<button
													type="button"
													class="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-emerald-700"
													onclick={() => markLoyerPaid(loyer.id!)}
												>
													Marquer payé
												</button>
											</div>
										</div>
									{/each}
								</div>
							</CardContent>
						</Card>
					{/if}

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
								loyers={scopedLoyers.slice(0, 10)}
								biens={scopedBiens}
								{loading}
								title="Journal de la SCI active"
								description="Historique opérationnel."
							/>
						</CardContent>
					</Card>
				</div>

				<!-- ─── Tab: Patrimoine ─── -->
			{:else if activeTab === 'patrimoine'}
				<div class="grid gap-6 xl:grid-cols-[1.25fr_1fr]">
					<div class="space-y-6">
						<SCIIdentityCard
							{activeSciProfile}
							{activeSciDetail}
							{scopedBiens}
							{bienMetrics}
							{detailLoading}
						/>
						<div id="dashboard-patrimoine" class="scroll-mt-28">
							<BienTable
								biens={scopedBiens}
								{loading}
								title="Patrimoine piloté"
								description="Vue consolidée des biens de la SCI active."
							/>
						</div>
					</div>
					<ChargesFiscalPanel
						totalRecordedCharges={activeSciDetail?.total_recorded_charges}
						chargesCount={activeSciDetail?.charges_count ?? 0}
						recentCharges={recentChargeFeed}
						{latestFiscalYear}
						{detailLoading}
					/>
				</div>

				<!-- ─── Tab: Documents ─── -->
			{:else if activeTab === 'documents'}
				<div class="grid gap-6 xl:grid-cols-2">
					<div id="dashboard-documents" class="scroll-mt-28">
						<QuitusGenerator
							loyers={scopedLoyers}
							biens={scopedBiens}
							sciName={activeSciProfile?.nom || activeSci?.nom || ''}
						/>
					</div>
					<Card>
						<CardHeader>
							<CardTitle class="text-lg">Fiscalité</CardTitle>
							<CardDescription>Exercices fiscaux de la SCI active.</CardDescription>
						</CardHeader>
						<CardContent>
							{#if latestFiscalYear}
								<div class="space-y-3">
									<div
										class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900"
									>
										<p class="text-xs font-semibold tracking-wider text-slate-500 uppercase">
											Exercice {latestFiscalYear.annee}
										</p>
										<div class="mt-2 grid grid-cols-3 gap-4">
											<div>
												<p class="text-xs text-slate-500">Revenus</p>
												<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
													{formatEur(latestFiscalYear.total_revenus ?? 0)}
												</p>
											</div>
											<div>
												<p class="text-xs text-slate-500">Charges</p>
												<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
													{formatEur(latestFiscalYear.total_charges ?? 0)}
												</p>
											</div>
											<div>
												<p class="text-xs text-slate-500">Résultat</p>
												<p
													class="text-sm font-semibold {(latestFiscalYear.resultat_fiscal ?? 0) >= 0
														? 'text-emerald-600'
														: 'text-rose-600'}"
												>
													{formatEur(latestFiscalYear.resultat_fiscal ?? 0)}
												</p>
											</div>
										</div>
									</div>
								</div>
							{:else}
								<p class="text-sm text-slate-500">Aucun exercice fiscal documenté.</p>
							{/if}
						</CardContent>
					</Card>
				</div>

				<!-- ─── Tab: Gouvernance ─── -->
			{:else if activeTab === 'gouvernance'}
				<div class="grid gap-6 xl:grid-cols-2">
					<AssociatesPanel associates={associateSummary} />
					<Card>
						<CardHeader>
							<CardTitle class="text-lg">Informations SCI</CardTitle>
							<CardDescription>Identité et gouvernance de la SCI active.</CardDescription>
						</CardHeader>
						<CardContent>
							{#if activeSciProfile}
								<div class="space-y-3">
									<div
										class="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800"
									>
										<span class="text-sm text-slate-500">Nom</span>
										<span class="text-sm font-medium text-slate-900 dark:text-slate-100"
											>{activeSciProfile.nom}</span
										>
									</div>
									{#if activeSciProfile.siren}
										<div
											class="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800"
										>
											<span class="text-sm text-slate-500">SIREN</span>
											<span class="text-sm font-medium text-slate-900 dark:text-slate-100"
												>{activeSciProfile.siren}</span
											>
										</div>
									{/if}
									{#if activeSciProfile.regime_fiscal}
										<div
											class="flex justify-between border-b border-slate-100 pb-2 dark:border-slate-800"
										>
											<span class="text-sm text-slate-500">Régime fiscal</span>
											<span class="text-sm font-medium text-slate-900 dark:text-slate-100"
												>{activeSciProfile.regime_fiscal}</span
											>
										</div>
									{/if}
									<div class="flex justify-between">
										<span class="text-sm text-slate-500">Rôle utilisateur</span>
										<span class="text-sm font-medium text-slate-900 dark:text-slate-100"
											>{mapAssociateRoleLabel(activeSciProfile.user_role ?? '')}</span
										>
									</div>
								</div>
							{:else}
								<p class="text-sm text-slate-500">
									Sélectionnez une SCI pour afficher ses informations.
								</p>
							{/if}
						</CardContent>
					</Card>
				</div>

				<!-- ─── Tab: Analytique ─── -->
			{:else if activeTab === 'analytique'}
				{#if loyers.length > 0}
					<div class="grid gap-6 lg:grid-cols-3">
						<CollectionChart loyers={scopedLoyers} />
						<RentTrendChart loyers={scopedLoyers} />
						<PortfolioAllocationChart {biens} {scis} />
					</div>
				{:else}
					<div
						class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-16 dark:border-slate-700"
					>
						<BarChart3 class="h-10 w-10 text-slate-400" />
						<p class="mt-3 text-sm text-slate-500">
							Saisissez des loyers pour visualiser les analytiques.
						</p>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</section>
