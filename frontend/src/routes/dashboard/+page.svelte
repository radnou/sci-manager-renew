<script lang="ts">
	import { onMount } from 'svelte';
	import {
		Building2,
		FileText,
		HandCoins,
		Landmark,
		ShieldCheck,
		TriangleAlert,
		Users
	} from 'lucide-svelte';
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
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import LoyerTable from '$lib/components/LoyerTable.svelte';
	import QuitusGenerator from '$lib/components/QuitusGenerator.svelte';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { calculateBienMetrics } from '$lib/high-value/biens';
	import { calculateLoyerMetrics, mapLoyerStatusLabel } from '$lib/high-value/loyers';
	import { calculatePortfolioMetrics, calculateSciScopeMetrics } from '$lib/high-value/portfolio';
	import {
		formatCompactNumber,
		formatEur,
		formatFrDate,
		formatPercent
	} from '$lib/high-value/formatters';
	import {
		formatApiErrorMessage,
		mapAssociateRoleLabel,
		mapChargeTypeLabel
	} from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

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
			title:
				scopedBiens.length === 0 ? 'Structurer le patrimoine' : 'Mettre à jour le portefeuille',
			description:
				scopedBiens.length === 0
					? 'Aucun bien n’est encore rattaché à la SCI active. Commence par documenter le premier actif.'
					: `${scopedBiens.length} biens rattachés à la SCI active. Vérifie les loyers et charges du mois.`,
			tone: scopedBiens.length === 0 ? 'warning' : 'default'
		},
		{
			title:
				loyerMetrics.lateCount > 0
					? 'Traiter les retards'
					: loyerMetrics.totalOutstanding > 0
						? 'Encaissements à sécuriser'
						: 'Suivi des encaissements sous contrôle',
			description:
				loyerMetrics.lateCount > 0
					? `${loyerMetrics.lateCount} loyer(s) en retard nécessitent une relance ou un arbitrage.`
					: loyerMetrics.totalOutstanding > 0
						? `${loyerMetrics.totalOutstandingLabel} restent en attente d’encaissement sur la SCI active.`
						: 'Tous les flux saisis sont encaissés. Tu peux préparer les quittances et la revue mensuelle.',
			tone:
				loyerMetrics.lateCount > 0
					? 'danger'
					: loyerMetrics.totalOutstanding > 0
						? 'warning'
						: 'success'
		},
		{
			title: associateSummary.length > 1 ? 'Coordonner les associés' : 'Gouvernance simple',
			description:
				associateSummary.length > 1
					? `${associateSummary.length} associés sont impliqués. Prépare un point de gouvernance avant les arbitrages.`
					: 'La SCI est portée par un seul associé référent. Les validations sont fluides.',
			tone: 'accent'
		}
	];
	$: commandTracks = [
		{
			id: 'dashboard-governance',
			label: 'Gouvernance',
			summary:
				associateSummary.length > 0
					? `${associateSummary.length} associé(s) documenté(s)`
					: 'Associés à documenter',
			detail: activeSciProfile?.user_role
				? `${mapAssociateRoleLabel(activeSciProfile.user_role)} connecté`
				: 'Rôle utilisateur à confirmer'
		},
		{
			id: 'dashboard-patrimoine',
			label: 'Patrimoine',
			summary: `${activeSciDetail?.biens_count ?? scopedBiens.length} bien(s) actifs`,
			detail: `Loyer cible ${formatEur(
				activeSciDetail?.total_monthly_rent ?? bienMetrics.totalMonthlyRent
			)}`
		},
		{
			id: 'dashboard-execution',
			label: 'Encaissements',
			summary: `Recouvrement ${formatPercent(collectionRate, '0%')}`,
			detail:
				loyerMetrics.lateCount > 0
					? `${loyerMetrics.lateCount} retard(s) à traiter`
					: loyerMetrics.totalOutstanding > 0
						? `${loyerMetrics.totalOutstandingLabel} à sécuriser`
						: 'Aucun retard détecté'
		},
		{
			id: 'dashboard-documents',
			label: 'Documents',
			summary: latestFiscalYear
				? `Exercice ${latestFiscalYear.annee} consolidé`
				: 'Clôture fiscale à préparer',
			detail:
				scopedLoyers.length > 0
					? `${scopedLoyers.length} loyer(s) saisi(s), quittances générables`
					: 'Aucun loyer saisi pour produire une quittance'
		}
	];

	$: if (resolvedActiveSciId) {
		setStoredActiveSciId(resolvedActiveSciId);
	}

	$: if (!resolvedActiveSciId) {
		activeSciDetail = null;
		detailLoading = false;
		detailErrorMessage = '';
		detailLoadedFor = '';
	} else if (detailLoadedFor !== resolvedActiveSciId) {
		detailLoadedFor = resolvedActiveSciId;
		void loadSciDetail(resolvedActiveSciId);
	}

	function statusLabel(status: SCIOverview['statut']) {
		if (!status) return 'À structurer';
		if (status === 'configuration') return 'À structurer';
		if (status === 'mise_en_service') return 'Mise en service';
		return 'En exploitation';
	}

	function statusClass(status: SCIOverview['statut']) {
		if (!status || status === 'configuration') {
			return 'bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-200';
		}
		if (status === 'mise_en_service') {
			return 'bg-cyan-100 text-cyan-900 dark:bg-cyan-950/40 dark:text-cyan-200';
		}
		return 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200';
	}

	function snapshotAlertLabel(snapshot: (typeof sciSnapshots)[number]) {
		if (snapshot.loyerMetrics.lateCount > 0) {
			return `${snapshot.loyerMetrics.lateCount} retard(s)`;
		}
		if (snapshot.loyerMetrics.totalOutstanding > 0) {
			return `${snapshot.loyerMetrics.totalOutstandingLabel} en attente`;
		}
		if (snapshot.biens.length === 0) {
			return 'Patrimoine à structurer';
		}
		return 'Sous contrôle';
	}

	function snapshotAlertClass(snapshot: (typeof sciSnapshots)[number]) {
		if (snapshot.loyerMetrics.lateCount > 0) {
			return 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200';
		}
		if (snapshot.loyerMetrics.totalOutstanding > 0) {
			return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200';
		}
		if (snapshot.biens.length === 0) {
			return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200';
		}
		return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200';
	}

	function activeSciStatus(status: SCIOverview['statut'] | null | undefined) {
		return statusClass(status ?? activeSciProfile?.statut ?? null);
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
				'Impossible de charger le dashboard spécifique de la SCI active.'
			);
		} finally {
			if (requestVersion !== detailRequestVersion) return;
			detailLoading = false;
		}
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Pilotage SCI • Cockpit exécutif</p>
		<h1 class="sci-page-title">Dashboard de portefeuille</h1>
		<p class="sci-page-subtitle">
			Une vue portefeuille de toutes les SCI accessibles par l’utilisateur. Sélectionne ensuite une
			SCI active pour entrer dans la lecture opérationnelle, la gouvernance et les flux.
		</p>
	</header>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
		<KpiCard
			label="SCI suivies"
			value={formatCompactNumber(portfolioMetrics.sciCount)}
			caption={`${portfolioMetrics.operationalSciCount} opérationnelle(s) dans le portefeuille`}
			trend={portfolioMetrics.attentionSciCount > 0 ? 'neutral' : 'up'}
			trendValue={portfolioMetrics.attentionSciCount > 0
				? `${portfolioMetrics.attentionSciCount} à surveiller`
				: 'sous contrôle'}
			tone={portfolioMetrics.attentionSciCount > 0 ? 'warning' : 'accent'}
			{loading}
		/>
		<KpiCard
			label="Patrimoine consolidé"
			value={portfolioMetrics.bienMetrics.count}
			caption="biens rattachés à l'ensemble du compte"
			trend="up"
			trendValue="multi-SCI"
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Loyer cible global"
			value={portfolioMetrics.bienMetrics.totalMonthlyRentLabel}
			caption="potentiel mensuel sur l'ensemble des SCI"
			trend="up"
			trendValue="portefeuille"
			tone="success"
			{loading}
		/>
		<KpiCard
			label="Encaissements sécurisés"
			value={portfolioMetrics.loyerMetrics.totalPaidLabel}
			caption={`reste à sécuriser ${portfolioMetrics.loyerMetrics.totalOutstandingLabel}`}
			trend={portfolioMetrics.loyerMetrics.totalOutstanding > 0 ? 'neutral' : 'up'}
			trendValue={portfolioMetrics.loyerMetrics.lateCount > 0
				? 'retards'
				: portfolioMetrics.loyerMetrics.totalOutstanding > 0
					? 'en attente'
					: 'conforme'}
			tone={portfolioMetrics.loyerMetrics.lateCount > 0
				? 'warning'
				: portfolioMetrics.loyerMetrics.totalOutstanding > 0
					? 'default'
					: 'success'}
			{loading}
		/>
	</div>

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.55fr_1fr]">
		<Card class="sci-section-card">
			<CardHeader>
				<CardTitle class="text-lg">Portefeuille multi-SCI</CardTitle>
				<CardDescription>
					Toutes les SCI accessibles par le compte. Clique sur une carte pour la rendre active dans
					le cockpit.
				</CardDescription>
			</CardHeader>
			<CardContent class="pt-0">
				{#if loading}
					<div class="grid gap-3 lg:grid-cols-2">
						{#each Array.from({ length: 4 }) as _}
							<div class="h-40 animate-pulse rounded-3xl bg-slate-100 dark:bg-slate-900"></div>
						{/each}
					</div>
				{:else if sciSnapshots.length === 0}
					<div
						class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
					>
						Aucune SCI accessible. Le dashboard portefeuille s’activera ici dès qu’une société sera
						liée au compte.
					</div>
				{:else}
					<div class="grid gap-3 lg:grid-cols-2">
						{#each sciSnapshots as snapshot (String(snapshot.sci.id))}
							<button
								type="button"
								class={`w-full rounded-[1.6rem] border p-4 text-left transition-colors ${
									String(snapshot.sci.id) === resolvedActiveSciId
										? 'border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-950'
										: 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700'
								}`}
								aria-pressed={String(snapshot.sci.id) === resolvedActiveSciId}
								onclick={() => {
									activeSciId = String(snapshot.sci.id);
									errorMessage = '';
								}}
							>
								<div class="flex items-start justify-between gap-3">
									<div>
										<p class="text-sm font-semibold">{snapshot.sci.nom}</p>
										<p class="mt-1 text-xs opacity-75">
											SIREN {snapshot.sci.siren || 'À compléter'}
										</p>
										<p class="mt-2 text-xs opacity-80">
											{snapshot.sci.user_role
												? `${mapAssociateRoleLabel(snapshot.sci.user_role)} connecté`
												: 'Rôle utilisateur à confirmer'}
										</p>
									</div>
									<span
										class={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ${statusClass(snapshot.sci.statut)}`}
									>
										{statusLabel(snapshot.sci.statut)}
									</span>
								</div>

								<div class="mt-4 grid grid-cols-3 gap-2 text-xs">
									<div>
										<p class="font-semibold">{snapshot.bienMetrics.count}</p>
										<p class="opacity-75">Biens</p>
									</div>
									<div>
										<p class="font-semibold">{snapshot.bienMetrics.totalMonthlyRentLabel}</p>
										<p class="opacity-75">Loyer cible</p>
									</div>
									<div>
										<span
											class={`inline-flex rounded-full px-2 py-1 font-semibold ${snapshotAlertClass(snapshot)}`}
										>
											{snapshotAlertLabel(snapshot)}
										</span>
									</div>
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</CardContent>
		</Card>

		<Card id="dashboard-governance" class="sci-section-card scroll-mt-28">
			<CardHeader>
				<CardTitle class="text-lg">Vue portefeuille</CardTitle>
				<CardDescription>
					Le cockpit global pour arbitrer entre structuration, trésorerie et priorité d’exécution.
				</CardDescription>
			</CardHeader>
			<CardContent class="space-y-4 pt-0">
				<div
					class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
				>
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						SCI opérationnelles
					</p>
					<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
						{portfolioMetrics.operationalSciCount}/{portfolioMetrics.sciCount}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						{portfolioMetrics.setupSciCount > 0
							? `${portfolioMetrics.setupSciCount} société(s) restent à structurer.`
							: 'Toutes les SCI du portefeuille sont mises en service ou en exploitation.'}
					</p>
				</div>

				<div
					class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
				>
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Trésorerie consolidée
					</p>
					<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
						{portfolioMetrics.loyerMetrics.totalOutstandingLabel}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						restent à encaisser sur {portfolioMetrics.loyerMetrics.totalRecordedLabel} saisis.
					</p>
				</div>

				<div
					class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
				>
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Points de vigilance
					</p>
					<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
						{portfolioMetrics.attentionSciCount}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						SCI demandent une action, avec {portfolioMetrics.loyerMetrics.lateCount} retard(s) identifié(s).
					</p>
				</div>

				<div class="flex flex-wrap gap-2">
					<a href="/scis">
						<Button variant="outline" size="sm">Voir les SCI</Button>
					</a>
					<a href="/biens">
						<Button size="sm">Gérer les biens</Button>
					</a>
					<a href="/loyers">
						<Button variant="outline" size="sm">Suivre les loyers</Button>
					</a>
				</div>
			</CardContent>
		</Card>
	</div>

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.8fr_1fr]">
		<div class="xl:col-span-2">
			<div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
				<div>
					<p class="sci-eyebrow">SCI active • Dashboard spécifique</p>
					<h2 class="text-2xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
						Cockpit d’exécution par cas d’usage
					</h2>
					<p class="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
						Le portefeuille reste en haut. Ici, la SCI active est organisée pour un usage opérateur
						desktop: gouvernance, patrimoine, encaissements et documents.
					</p>
				</div>
			</div>

			{#if detailErrorMessage}
				<p class="sci-inline-alert sci-inline-alert-error">{detailErrorMessage}</p>
			{/if}
		</div>

		<Card class="sci-section-card overflow-hidden">
			<CardContent class="relative p-0">
				<div
					class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-cyan-500 via-sky-400 to-emerald-500"
				></div>
				<div class="grid gap-6 p-6 lg:grid-cols-[1.4fr_1fr]">
					<div class="space-y-5">
						<div class="flex flex-wrap items-start justify-between gap-4">
							<div class="space-y-3">
								<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
									SCI active
								</p>
								<div class="flex flex-wrap items-center gap-2">
									<span
										class={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${activeSciStatus(activeSciProfile?.statut)}`}
									>
										{statusLabel(activeSciProfile?.statut)}
									</span>
									<span
										class="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
									>
										Régime {activeSciProfile?.regime_fiscal || 'IR'}
									</span>
								</div>
								<h2 class="text-3xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
									{activeSciProfile?.nom || 'SCI à sélectionner'}
								</h2>
								<p class="max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
									{#if activeSciProfile}
										Lecture d’exécution de la SCI sélectionnée: identité, gouvernance, encaissements
										et documents à produire.
									{:else}
										Sélectionne une SCI depuis la vue portefeuille pour ouvrir le détail
										d’exécution.
									{/if}
								</p>
							</div>

							{#if scis.length > 1}
								<label class="sci-field min-w-[16rem]">
									<span class="sci-field-label">Basculer la SCI active</span>
									<select
										id="dashboard-active-sci"
										name="dashboard-active-sci"
										class="sci-select"
										bind:value={activeSciId}
										aria-label="SCI active"
									>
										{#each scis as sci (String(sci.id))}
											<option value={String(sci.id)}>{sci.nom}</option>
										{/each}
									</select>
								</label>
							{/if}
						</div>

						<div class="grid gap-3 sm:grid-cols-3">
							<div
								class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
							>
								<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
									<Landmark class="h-4 w-4" />
									<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Identité</p>
								</div>
								<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
									SIREN {activeSciProfile?.siren || 'À compléter'}
								</p>
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
									{activeSciProfile?.user_role
										? `${mapAssociateRoleLabel(activeSciProfile.user_role)} connecté`
										: 'Rôle utilisateur à confirmer'}
								</p>
							</div>

							<div
								class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
							>
								<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
									<Users class="h-4 w-4" />
									<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">
										Gouvernance
									</p>
								</div>
								<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
									{activeSciProfile?.associes_count || 0} associé(s)
								</p>
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
									Part moyenne {formatPercent(avgAssociateShare, 'N/A')}
								</p>
							</div>

							<div
								class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
							>
								<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
									<ShieldCheck class="h-4 w-4" />
									<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">
										Santé SCI active
									</p>
								</div>
								<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
									Recouvrement {formatPercent(collectionRate, '0%')}
								</p>
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
									{loyerMetrics.lateCount > 0
										? `${loyerMetrics.lateCount} ligne(s) à traiter`
										: loyerMetrics.totalOutstanding > 0
											? `${loyerMetrics.totalOutstandingLabel} restent à sécuriser`
											: 'Aucun retard détecté'}
								</p>
							</div>
						</div>
					</div>

					<div
						class="rounded-[1.5rem] border border-slate-200 bg-slate-50/90 p-5 dark:border-slate-700 dark:bg-slate-900"
					>
						<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
							<TriangleAlert class="h-4 w-4" />
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">
								Postes de pilotage
							</p>
						</div>
						<p class="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
							Le dashboard spécifique s’organise par cas d’usage. Chaque bloc ci-dessous renvoie
							vers une zone claire du cockpit.
						</p>
						<div class="mt-4 space-y-3">
							{#each commandTracks as track}
								<a
									href={`#${track.id}`}
									class="group block rounded-2xl border border-slate-200 bg-white p-4 transition-colors hover:border-slate-300 dark:border-slate-700 dark:bg-slate-950 dark:hover:border-slate-600"
								>
									<div class="flex items-start justify-between gap-3">
										<div>
											<p
												class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
											>
												{track.label}
											</p>
											<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
												{track.summary}
											</p>
											<p class="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
												{track.detail}
											</p>
										</div>
										<span
											class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-700 transition-colors group-hover:bg-slate-900 group-hover:text-white dark:bg-slate-800 dark:text-slate-200 dark:group-hover:bg-slate-100 dark:group-hover:text-slate-950"
										>
											Voir
										</span>
									</div>
								</a>
							{/each}
						</div>
						<div class="mt-5">
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
								À traiter maintenant
							</p>
						</div>
						<div class="mt-3 space-y-3">
							{#each priorities as item}
								<div
									class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950"
								>
									<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
										{item.title}
									</p>
									<p class="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
										{item.description}
									</p>
								</div>
							{/each}
						</div>
						<div class="mt-4 flex flex-wrap gap-2">
							<a href="/scis">
								<Button variant="outline" size="sm">Voir les SCI</Button>
							</a>
							<a href="/biens">
								<Button size="sm">Gérer les biens</Button>
							</a>
							<a href="/loyers">
								<Button variant="outline" size="sm">Suivre les loyers</Button>
							</a>
						</div>
					</div>
				</div>
			</CardContent>
		</Card>

		<Card class="sci-section-card">
			<CardHeader>
				<CardTitle class="flex items-center gap-2 text-lg">
					<Users class="h-5 w-5 text-cyan-600" />
					Associés et gouvernance
				</CardTitle>
				<CardDescription>
					Répartition du capital et rôle opérationnel sur la SCI active.
				</CardDescription>
			</CardHeader>
			<CardContent class="space-y-3">
				{#if associateSummary.length === 0}
					<p
						class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
					>
						Aucun associé disponible sur la SCI active.
					</p>
				{:else}
					{#each associateSummary as associe (String(associe.id))}
						<div
							class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
						>
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
										{associe.nom}
									</p>
									<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
										{associe.email || 'Email non renseigné'}
									</p>
								</div>
								<span
									class="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-semibold text-white dark:bg-slate-100 dark:text-slate-950"
								>
									{associe.part ? formatPercent(associe.part) : 'Part N/A'}
								</span>
							</div>
							<p class="mt-3 text-xs font-semibold tracking-[0.18em] text-slate-500 uppercase">
								{mapAssociateRoleLabel(associe.role)}
							</p>
						</div>
					{/each}
				{/if}
			</CardContent>
		</Card>
	</div>

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.25fr_1fr]">
		<Card class="sci-section-card">
			<CardHeader>
				<CardTitle class="flex items-center gap-2 text-lg">
					<Landmark class="h-5 w-5 text-sky-600" />
					Fiche d’identité SCI active
				</CardTitle>
				<CardDescription>
					Les caractéristiques centrales de la société sélectionnée, utiles pour les arbitrages et
					la coordination.
				</CardDescription>
			</CardHeader>
			<CardContent class="pt-0">
				{#if detailLoading}
					<div class="grid gap-3 md:grid-cols-2">
						{#each Array.from({ length: 4 }) as _}
							<div class="h-24 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
						{/each}
					</div>
				{:else}
					<div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
						<div
							class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
						>
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
								Société
							</p>
							<p class="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
								SIREN {activeSciProfile?.siren || 'À compléter'}
							</p>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								{statusLabel(activeSciProfile?.statut)}
							</p>
						</div>
						<div
							class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
						>
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
								Gouvernance
							</p>
							<p class="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
								{activeSciProfile?.user_role
									? mapAssociateRoleLabel(activeSciProfile.user_role)
									: 'Rôle à confirmer'}
							</p>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								Part détenue {formatPercent(activeSciProfile?.user_part, 'N/A')}
							</p>
						</div>
						<div
							class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
						>
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
								Patrimoine
							</p>
							<p class="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
								{activeSciDetail?.biens_count ?? scopedBiens.length} bien(s)
							</p>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								Loyer cible {formatEur(
									activeSciDetail?.total_monthly_rent ?? bienMetrics.totalMonthlyRent
								)}
							</p>
						</div>
						<div
							class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
						>
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
								Documentation
							</p>
							<p class="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
								{activeSciDetail?.fiscalite?.length || 0} exercice(s)
							</p>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								{activeSciDetail?.charges_count ?? 0} charge(s) documentée(s)
							</p>
						</div>
					</div>
				{/if}
			</CardContent>
		</Card>

		<Card class="sci-section-card">
			<CardHeader>
				<CardTitle class="flex items-center gap-2 text-lg">
					<FileText class="h-5 w-5 text-emerald-600" />
					Charges et fiscalité
				</CardTitle>
				<CardDescription>
					Les derniers signaux spécifiques à la SCI active, pour la clôture et la conformité.
				</CardDescription>
			</CardHeader>
			<CardContent class="space-y-4 pt-0">
				{#if detailLoading}
					<div class="space-y-3">
						{#each Array.from({ length: 3 }) as _}
							<div class="h-20 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
						{/each}
					</div>
				{:else}
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Charges documentées
						</p>
						<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
							{formatEur(activeSciDetail?.total_recorded_charges, 'N/A')}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							{activeSciDetail?.charges_count ?? 0} mouvement(s) documenté(s) sur la SCI active.
						</p>
					</div>

					<div class="space-y-3">
						{#if recentChargeFeed.length}
							{#each recentChargeFeed.slice(0, 2) as charge (String(charge.id || `${charge.id_bien}-${charge.date_paiement}`))}
								<div
									class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950"
								>
									<div class="flex items-center justify-between gap-3">
										<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
											{mapChargeTypeLabel(charge.type_charge)}
										</p>
										<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
											{formatEur(charge.montant, 'N/A')}
										</p>
									</div>
									<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
										Payée le {formatFrDate(charge.date_paiement)}
									</p>
								</div>
							{/each}
						{:else}
							<div
								class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
							>
								Aucune charge récente documentée pour cette SCI.
							</div>
						{/if}
					</div>

					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Dernier exercice fiscal
						</p>
						{#if latestFiscalYear}
							<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
								Exercice {latestFiscalYear.annee}
							</p>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								Résultat {formatEur(latestFiscalYear.resultat_fiscal, 'N/A')} • revenus {formatEur(
									latestFiscalYear.total_revenus,
									'N/A'
								)}
							</p>
						{:else}
							<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
								Aucun exercice consolidé pour la SCI active.
							</p>
						{/if}
					</div>
				{/if}
			</CardContent>
		</Card>
	</div>

	<div class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
		<KpiCard
			label="Biens actifs"
			value={bienMetrics.count}
			caption="actifs rattachés à la SCI"
			trend="up"
			trendValue="patrimoine"
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Loyers de la SCI active"
			value={bienMetrics.totalMonthlyRentLabel}
			caption="potentiel mensuel sécurisé"
			trend="up"
			trendValue="revenus"
			tone="success"
			{loading}
		/>
		<KpiCard
			label="Flux encaissés"
			value={loyerMetrics.totalPaidLabel}
			caption="encaissements réellement payés"
			trend="neutral"
			trendValue={loyerMetrics.totalOutstanding > 0 ? 'à suivre' : 'sécurisé'}
			tone="default"
			{loading}
		/>
		<KpiCard
			label="Recouvrement"
			value={formatPercent(collectionRate, '0%')}
			caption={`${loyerMetrics.totalPaidLabel} encaissés sur ${loyerMetrics.totalRecordedLabel}`}
			trend={loyerMetrics.lateCount > 0
				? 'down'
				: loyerMetrics.totalOutstanding > 0
					? 'neutral'
					: 'up'}
			trendValue={loyerMetrics.lateCount > 0
				? 'vigilance'
				: loyerMetrics.totalOutstanding > 0
					? 'à compléter'
					: 'conforme'}
			tone={loyerMetrics.lateCount > 0
				? 'warning'
				: loyerMetrics.totalOutstanding > 0
					? 'default'
					: 'accent'}
			{loading}
		/>
	</div>

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.8fr_1fr]">
		<div class="space-y-6">
			<div id="dashboard-patrimoine" class="scroll-mt-28">
				<BienTable
					biens={scopedBiens.slice(0, 6)}
					{loading}
					title="Patrimoine piloté"
					description="Vue consolidée des biens de la SCI active, utile pour les arbitrages et la revue mensuelle."
				/>
			</div>

			<Card id="dashboard-execution" class="sci-section-card scroll-mt-28">
				<CardHeader>
					<CardTitle class="flex items-center gap-2 text-lg">
						<HandCoins class="h-5 w-5 text-emerald-600" />
						Mouvements et alertes
					</CardTitle>
					<CardDescription>
						Les dernières lignes utiles pour la trésorerie et la production des quittances.
					</CardDescription>
				</CardHeader>
				<CardContent>
					<LoyerTable
						loyers={scopedLoyers.slice(0, 8)}
						biens={scopedBiens}
						{loading}
						title="Journal de la SCI active"
						description="Historique opérationnel sans identifiants techniques."
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

			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="flex items-center gap-2 text-lg">
						<FileText class="h-5 w-5 text-sky-600" />
						Rituels opérateur
					</CardTitle>
					<CardDescription>
						Les repères desktop pour la revue hebdomadaire, la quittance et la clôture.
					</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Dernier flux locatif
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{latestLoyer
								? `${formatFrDate(latestLoyer.date_loyer)} • ${formatEur(latestLoyer.montant)}`
								: 'Aucun flux saisi'}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							{latestLoyer
								? mapLoyerStatusLabel(latestLoyer.statut)
								: 'Le journal locatif s’activera ici dès la première saisie.'}
						</p>
					</div>
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Cadence documentaire
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{scopedLoyers.length > 0
								? 'Quittances générables immédiatement'
								: 'Aucune quittance à produire'}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							{scopedLoyers.length > 0
								? `${scopedLoyers.length} loyer(s) saisi(s) sur la SCI active.`
								: 'Le module PDF attend au moins un loyer enregistré.'}
						</p>
					</div>
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Charges récurrentes
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{formatEur(monthlyPropertyCharges)}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							charges mensuelles renseignées sur les biens de la SCI active.
						</p>
					</div>
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
							Clôture fiscale
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{latestFiscalYear ? `Exercice ${latestFiscalYear.annee}` : 'Aucun exercice consolidé'}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							{latestCharge
								? `${mapChargeTypeLabel(latestCharge.type_charge)} • payée le ${formatFrDate(latestCharge.date_paiement)}`
								: 'Aucune charge récente documentée.'}
						</p>
					</div>
				</CardContent>
			</Card>
		</div>
	</div>
</section>
