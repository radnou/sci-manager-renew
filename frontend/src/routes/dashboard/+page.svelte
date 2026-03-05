<script lang="ts">
	import { onMount } from 'svelte';
	import { Building2, FileText, HandCoins, Landmark, ShieldCheck, TriangleAlert, Users } from 'lucide-svelte';
	import { fetchBiens, fetchLoyers, fetchScis, type Bien, type Loyer, type SCIOverview } from '$lib/api';
	import BienTable from '$lib/components/BienTable.svelte';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import LoyerTable from '$lib/components/LoyerTable.svelte';
	import QuitusGenerator from '$lib/components/QuitusGenerator.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { calculateBienMetrics } from '$lib/high-value/biens';
	import { calculateLoyerMetrics, mapLoyerStatusLabel } from '$lib/high-value/loyers';
	import { formatCompactNumber, formatEur, formatPercent } from '$lib/high-value/formatters';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let biens: Bien[] = [];
	let loyers: Loyer[] = [];
	let scis: SCIOverview[] = [];
	let activeSciId = '';
	let loading = true;
	let errorMessage = '';

	$: resolvedActiveSciId =
		activeSciId && scis.some((sci) => String(sci.id) === activeSciId) ? activeSciId : String(scis[0]?.id || '');
	$: activeSci = scis.find((sci) => String(sci.id) === resolvedActiveSciId) ?? null;
	$: if (resolvedActiveSciId) {
		setStoredActiveSciId(resolvedActiveSciId);
	}

	function loyerBelongsToActiveSci(loyer: Loyer) {
		if (!activeSci) {
			return true;
		}

		if (loyer.id_sci) {
			return String(loyer.id_sci) === String(activeSci.id);
		}

		const bien = biens.find((entry) => String(entry.id || '') === String(loyer.id_bien || ''));
		return String(bien?.id_sci || '') === String(activeSci.id);
	}

	$: scopedBiens = activeSci
		? biens.filter((bien) => String(bien.id_sci || '') === String(activeSci.id))
		: biens;
	$: scopedLoyers = activeSci ? loyers.filter(loyerBelongsToActiveSci) : loyers;
	$: bienMetrics = calculateBienMetrics(scopedBiens);
	$: loyerMetrics = calculateLoyerMetrics(scopedLoyers);
	$: paidCount = scopedLoyers.filter((loyer) => String(loyer.statut || '').toLowerCase() === 'paye').length;
	$: collectionRate = scopedLoyers.length > 0 ? (paidCount / scopedLoyers.length) * 100 : 0;
	$: avgAssociateShare =
		activeSci && activeSci.associes_count && activeSci.associes_count > 0
			? 100 / activeSci.associes_count
			: 0;
	$: associateSummary = activeSci?.associes ?? [];
	$: priorities = [
		{
			title: scopedBiens.length === 0 ? 'Structurer le patrimoine' : 'Mettre à jour le portefeuille',
			description:
				scopedBiens.length === 0
					? 'Aucun bien n’est encore rattaché à la SCI active. Commence par documenter le premier actif.'
					: `${scopedBiens.length} biens rattachés à la SCI active. Vérifie les loyers et charges du mois.`,
			tone: scopedBiens.length === 0 ? 'warning' : 'default'
		},
		{
			title: loyerMetrics.lateCount > 0 ? 'Traiter les retards' : 'Suivi des encaissements sous contrôle',
			description:
				loyerMetrics.lateCount > 0
					? `${loyerMetrics.lateCount} loyer(s) en retard nécessitent une relance ou un arbitrage.`
					: 'Aucun retard détecté. Tu peux préparer les quittances et la revue mensuelle.',
			tone: loyerMetrics.lateCount > 0 ? 'danger' : 'success'
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
		if (status === 'mise_en_service') return 'bg-cyan-100 text-cyan-900 dark:bg-cyan-950/40 dark:text-cyan-200';
		return 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200';
	}

	function associateRoleLabel(role: string | null | undefined) {
		if (!role) return 'Associé';
		if (role.toLowerCase().includes('ger')) return 'Gérant';
		return role.charAt(0).toUpperCase() + role.slice(1);
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
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Impossible de charger le cockpit SCI.';
		} finally {
			loading = false;
		}
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Pilotage SCI • Cockpit exécutif</p>
		<h1 class="sci-page-title">Dashboard de portefeuille</h1>
		<p class="sci-page-subtitle">
			Un cockpit centré sur la SCI active, la gouvernance, les encaissements et les documents à produire, sans
			exposer les identifiants techniques.
		</p>
	</header>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	<div class="grid gap-6 xl:grid-cols-[1.8fr_1fr]">
		<Card class="sci-section-card overflow-hidden">
			<CardContent class="relative p-0">
				<div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-cyan-500 via-sky-400 to-emerald-500"></div>
				<div class="grid gap-6 p-6 lg:grid-cols-[1.4fr_1fr]">
					<div class="space-y-5">
						<div class="flex flex-wrap items-start justify-between gap-4">
							<div class="space-y-3">
								<div class="flex flex-wrap items-center gap-2">
									<span class={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusClass(activeSci?.statut)}`}>
										{statusLabel(activeSci?.statut)}
									</span>
									<span class="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
										Régime {activeSci?.regime_fiscal || 'IR'}
									</span>
								</div>
								<h2 class="text-3xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
									{activeSci?.nom || 'SCI à sélectionner'}
								</h2>
								<p class="max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
									{#if activeSci}
										Vision synthétique de la société civile immobilière active, de ses associés et des flux à sécuriser cette semaine.
									{:else}
										Le cockpit affichera ici la SCI active dès qu’une entité sera accessible depuis ton compte.
									{/if}
								</p>
							</div>

							{#if scis.length > 1}
								<label class="sci-field min-w-[16rem]">
									<span class="sci-field-label">SCI active</span>
									<select id="dashboard-active-sci" name="dashboard-active-sci" class="sci-select" bind:value={activeSciId} aria-label="SCI active">
										{#each scis as sci (String(sci.id))}
											<option value={String(sci.id)}>{sci.nom}</option>
										{/each}
									</select>
								</label>
							{/if}
						</div>

						<div class="grid gap-3 sm:grid-cols-3">
							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
									<Landmark class="h-4 w-4" />
									<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Identité</p>
								</div>
								<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
									SIREN {activeSci?.siren || 'À compléter'}
								</p>
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
									{activeSci?.user_role ? `${associateRoleLabel(activeSci.user_role)} connecté` : 'Rôle utilisateur à confirmer'}
								</p>
							</div>

							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
									<Users class="h-4 w-4" />
									<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Gouvernance</p>
								</div>
								<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
									{activeSci?.associes_count || 0} associé(s)
								</p>
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
									Part moyenne {formatPercent(avgAssociateShare, 'N/A')}
								</p>
							</div>

							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
									<ShieldCheck class="h-4 w-4" />
									<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Santé portefeuille</p>
								</div>
								<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
									Recouvrement {formatPercent(collectionRate, '0%')}
								</p>
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
									{loyerMetrics.lateCount > 0 ? `${loyerMetrics.lateCount} ligne(s) à traiter` : 'Aucun retard détecté'}
								</p>
							</div>
						</div>
					</div>

					<div class="rounded-[1.5rem] border border-slate-200 bg-slate-50/90 p-5 dark:border-slate-700 dark:bg-slate-900">
						<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
							<TriangleAlert class="h-4 w-4" />
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Actions prioritaires</p>
						</div>
						<div class="mt-4 space-y-3">
							{#each priorities as item}
								<div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
									<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.title}</p>
									<p class="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{item.description}</p>
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
				<CardDescription>Répartition du capital et rôle opérationnel sur la SCI active.</CardDescription>
			</CardHeader>
			<CardContent class="space-y-3">
				{#if associateSummary.length === 0}
					<p class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
						Aucun associé disponible sur la SCI active.
					</p>
				{:else}
					{#each associateSummary as associe (String(associe.id))}
						<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">{associe.nom}</p>
									<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{associe.email || 'Email non renseigné'}</p>
								</div>
								<span class="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-semibold text-white dark:bg-slate-100 dark:text-slate-950">
									{associe.part ? formatPercent(associe.part) : 'Part N/A'}
								</span>
							</div>
							<p class="mt-3 text-xs font-semibold tracking-[0.18em] text-slate-500 uppercase">
								{associateRoleLabel(associe.role)}
							</p>
						</div>
					{/each}
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
			trendValue="portefeuille"
			tone="accent"
			{loading}
		/>
		<KpiCard
			label="Loyers du portefeuille"
			value={bienMetrics.totalMonthlyRentLabel}
			caption="potentiel mensuel sécurisé"
			trend="up"
			trendValue="revenus"
			tone="success"
			{loading}
		/>
		<KpiCard
			label="Flux encaissés"
			value={loyerMetrics.totalCollectedLabel}
			caption="encaissements saisis"
			trend="neutral"
			trendValue={formatCompactNumber(scopedLoyers.length)}
			tone="default"
			{loading}
		/>
		<KpiCard
			label="Recouvrement"
			value={formatPercent(collectionRate, '0%')}
			caption={`${paidCount} ligne(s) payée(s) sur ${scopedLoyers.length}`}
			trend={loyerMetrics.lateCount > 0 ? 'down' : 'up'}
			trendValue={loyerMetrics.lateCount > 0 ? 'vigilance' : 'conforme'}
			tone={loyerMetrics.lateCount > 0 ? 'warning' : 'accent'}
			{loading}
		/>
	</div>

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.8fr_1fr]">
		<div class="space-y-6">
			<BienTable
				biens={scopedBiens.slice(0, 6)}
				{loading}
				title="Patrimoine piloté"
				description="Vue consolidée des biens de la SCI active, utile pour les arbitrages et la revue mensuelle."
			/>

			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="flex items-center gap-2 text-lg">
						<HandCoins class="h-5 w-5 text-emerald-600" />
						Mouvements et alertes
					</CardTitle>
					<CardDescription>Les dernières lignes utiles pour la trésorerie et la production des quittances.</CardDescription>
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
			<QuitusGenerator loyers={scopedLoyers} biens={scopedBiens} />

			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="flex items-center gap-2 text-lg">
						<FileText class="h-5 w-5 text-sky-600" />
						Repères opérationnels
					</CardTitle>
					<CardDescription>Résumé métier pour la revue hebdomadaire de la SCI.</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Statut dominant</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{scopedLoyers.length > 0 ? mapLoyerStatusLabel(scopedLoyers[0].statut) : 'Aucun flux saisi'}
						</p>
					</div>
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Patrimoine</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{scopedBiens.length > 0 ? `${scopedBiens.length} bien(s) à jour` : 'Patrimoine à documenter'}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							Charges mensuelles {formatEur(scopedBiens.reduce((sum, bien) => sum + (bien.charges ?? 0), 0))}
						</p>
					</div>
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Conformité documentaire</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{scopedLoyers.length > 0 ? 'Quittances générables immédiatement' : 'Aucune quittance à produire'}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							Le module PDF est centré sur les loyers réellement saisis.
						</p>
					</div>
				</CardContent>
			</Card>
		</div>
	</div>
</section>
