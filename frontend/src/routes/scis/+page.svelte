<script lang="ts">
	import { onMount } from 'svelte';
	import { Building2, FileText, HandCoins, Landmark, ShieldCheck, Users } from 'lucide-svelte';
	import {
		createSci,
		fetchSciDetail,
		fetchScis,
		fetchSubscriptionEntitlements,
		type SCIDetail,
		type SCIOverview,
		type SubscriptionEntitlements
	} from '$lib/api';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { featureFlags } from '$lib/config/features';
	import { mapBienTypeLabel } from '$lib/high-value/biens';
	import {
		formatCompactNumber,
		formatEur,
		formatFrDate,
		formatPercent
	} from '$lib/high-value/formatters';
	import { mapLoyerStatusLabel } from '$lib/high-value/loyers';
	import {
		formatApiErrorMessage,
		mapAssociateRoleLabel,
		mapChargeTypeLabel
	} from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let scis = $state<SCIOverview[]>([]);
	let detail = $state<SCIDetail | null>(null);
	let activeSciId = $state('');
	let loading = $state(true);
	let detailLoading = $state(true);
	let errorMessage = $state('');
	let detailLoadedFor = $state('');
	let subscription = $state<SubscriptionEntitlements | null>(null);
	let sciFormNom = $state('');
	let sciFormSiren = $state('');
	let sciFormRegime = $state<'IR' | 'IS'>('IR');
	let creatingSci = $state(false);
	const multiSciDashboardV2Enabled = featureFlags.multiSciDashboardV2;

	const resolvedActiveSciId = $derived(
		activeSciId && scis.some((sci) => String(sci.id) === activeSciId)
			? activeSciId
			: String(scis[0]?.id || '')
	);
	const activeSci = $derived(scis.find((sci) => String(sci.id) === resolvedActiveSciId) ?? null);
	const collectionRate = $derived.by(() => {
		const paid = detail?.paid_loyers_total ?? 0;
		const pending = detail?.pending_loyers_total ?? 0;
		const total = paid + pending;
		return total > 0 ? (paid / total) * 100 : 0;
	});

	$effect(() => {
		if (!resolvedActiveSciId) {
			return;
		}

		setStoredActiveSciId(resolvedActiveSciId);
	});

	$effect(() => {
		if (!resolvedActiveSciId || detailLoadedFor === resolvedActiveSciId) {
			return;
		}

		detailLoadedFor = resolvedActiveSciId;
		void loadSciDetail(resolvedActiveSciId);
	});

	onMount(async () => {
		if (!multiSciDashboardV2Enabled) {
			loading = false;
			detailLoading = false;
			return;
		}
		await loadScis();
	});

	async function loadScis() {
		loading = true;
		errorMessage = '';

		try {
			const [nextScis, nextSubscription] = await Promise.all([
				fetchScis(),
				fetchSubscriptionEntitlements()
			]);
			scis = Array.isArray(nextScis) ? nextScis : [];
			subscription = nextSubscription;
			const storedActiveSciId = getStoredActiveSciId();
			activeSciId =
				(storedActiveSciId &&
					nextScis.some((sci) => String(sci.id) === storedActiveSciId) &&
					storedActiveSciId) ||
				String(nextScis[0]?.id || '');
			if (!nextScis.length) {
				detail = null;
			}
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de charger le portefeuille SCI.');
		} finally {
			loading = false;
		}
	}

	async function handleCreateSci() {
		if (!sciFormNom.trim()) {
			errorMessage = 'Le nom de la SCI est requis.';
			return;
		}

		creatingSci = true;
		errorMessage = '';
		try {
			const created = await createSci({
				nom: sciFormNom.trim(),
				siren: sciFormSiren.trim() || null,
				regime_fiscal: sciFormRegime
			});
			scis = [...scis, created].sort((left, right) => left.nom.localeCompare(right.nom, 'fr'));
			activeSciId = String(created.id);
			sciFormNom = '';
			sciFormSiren = '';
			subscription = await fetchSubscriptionEntitlements();
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible de créer la SCI.');
		} finally {
			creatingSci = false;
		}
	}

	async function loadSciDetail(sciId: string) {
		detailLoading = true;

		try {
			detail = await fetchSciDetail(sciId);
		} catch (error) {
			detail = null;
			errorMessage = formatApiErrorMessage(
				error,
				'Impossible de charger la fiche détaillée de la SCI.'
			);
		} finally {
			detailLoading = false;
		}
	}

	function statusLabel(status: SCIOverview['statut']) {
		if (!status || status === 'configuration') return 'À structurer';
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

	function bienLabel(bienId: string | number | null | undefined) {
		const bien = detail?.biens?.find((entry) => String(entry.id || '') === String(bienId || ''));
		if (!bien) {
			return 'Bien non identifié';
		}
		if (bien.ville) {
			return `${bien.adresse} • ${bien.ville}`;
		}
		return bien.adresse;
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Portefeuille SCI • Consolidation multi-entités</p>
		<h1 class="sci-page-title">Pilotage des SCI</h1>
		<p class="sci-page-subtitle">
			Une vue structurée de toutes les SCI accessibles par le compte, avec identité, gouvernance,
			patrimoine, charges et flux récents.
		</p>
	</header>

	{#if !multiSciDashboardV2Enabled}
		<div class="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-[0_25px_80px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-950">
			<p class="text-[0.72rem] font-semibold tracking-[0.2em] text-slate-500 uppercase">
				Rollout contrôlé
			</p>
			<h2 class="mt-3 font-serif text-3xl text-slate-950 dark:text-slate-50">
				Le portefeuille multi-SCI V2 est désactivé
			</h2>
			<p class="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
				Ce workspace n’est pas exposé dans l’environnement courant. Continue le pilotage depuis
				le cockpit, les biens et les loyers pendant que le rollout reste fermé.
			</p>
			<div class="mt-6 flex flex-wrap gap-3">
				<a href="/dashboard"><Button>Ouvrir le cockpit</Button></a>
				<a href="/biens"><Button variant="outline">Gérer les biens</Button></a>
				<a href="/loyers"><Button variant="outline">Suivre les loyers</Button></a>
			</div>
		</div>
	{:else}
		{#if errorMessage}
			<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
		{/if}

		<div class="grid gap-6 xl:grid-cols-[22rem_1fr]">
			<Card class="sci-section-card h-fit">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">SCI du portefeuille</CardTitle>
					<CardDescription
						>Sélectionne une entité pour afficher sa fiche d’identité complète.</CardDescription
					>
				</div>
			</CardHeader>
			<CardContent class="space-y-4 pt-0">
				{#if subscription}
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Capacité active</p>
						<p class="mt-2 font-semibold text-slate-900 dark:text-slate-100">{subscription.plan_name}</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							{subscription.max_scis == null ? 'SCI illimitées' : `${subscription.current_scis}/${subscription.max_scis} SCI`}
							•
							{subscription.max_biens == null ? 'Biens illimités' : `${subscription.current_biens}/${subscription.max_biens} biens`}
						</p>
					</div>
					<div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
						<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">Ajouter une SCI</p>
						<div class="mt-3 space-y-3">
							<label class="sci-field">
								<span class="sci-field-label">Nom</span>
								<Input bind:value={sciFormNom} placeholder="SCI Patrimoine Belleville" />
							</label>
							<label class="sci-field">
								<span class="sci-field-label">SIREN</span>
								<Input bind:value={sciFormSiren} placeholder="123456789" inputmode="numeric" />
							</label>
							<label class="sci-field">
								<span class="sci-field-label">Régime fiscal</span>
								<select bind:value={sciFormRegime} class="sci-select">
									<option value="IR">IR</option>
									<option value="IS">IS</option>
								</select>
							</label>
							<Button disabled={creatingSci} onclick={handleCreateSci}>
								{creatingSci ? 'Création en cours...' : 'Créer la SCI'}
							</Button>
						</div>
					</div>
				{/if}
				{#if loading}
					<div class="space-y-3">
						{#each Array.from({ length: 3 }) as _}
							<div class="h-24 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
						{/each}
					</div>
				{:else if scis.length === 0}
					<div
						class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
					>
						Aucune SCI accessible. Le portefeuille se remplira ici dès qu’une société sera liée au
						compte.
					</div>
				{:else}
					<div class="space-y-3">
						{#each scis as sci (String(sci.id))}
							<button
								type="button"
								class={`w-full rounded-2xl border p-4 text-left transition-colors ${
									String(sci.id) === resolvedActiveSciId
										? 'border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-950'
										: 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700'
								}`}
								onclick={() => {
									activeSciId = String(sci.id);
									errorMessage = '';
								}}
								aria-pressed={String(sci.id) === resolvedActiveSciId}
							>
								<div class="flex items-start justify-between gap-3">
									<div>
										<p class="text-sm font-semibold">{sci.nom}</p>
										<p class="mt-1 text-xs opacity-75">SIREN {sci.siren || 'À compléter'}</p>
									</div>
									<span
										class={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ${statusClass(sci.statut)}`}
									>
										{statusLabel(sci.statut)}
									</span>
								</div>
								<div class="mt-4 grid grid-cols-3 gap-2 text-xs opacity-80">
									<div>
										<p class="font-semibold">{sci.associes_count || 0}</p>
										<p>Associés</p>
									</div>
									<div>
										<p class="font-semibold">{sci.biens_count || 0}</p>
										<p>Biens</p>
									</div>
									<div>
										<p class="font-semibold">{sci.loyers_count || 0}</p>
										<p>Loyers</p>
									</div>
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</CardContent>
		</Card>

		<div class="space-y-6">
			<Card class="sci-section-card overflow-hidden">
				<CardContent class="p-0">
					<div class="h-1 bg-gradient-to-r from-cyan-500 via-sky-400 to-emerald-500"></div>
					<div class="grid gap-6 p-6 lg:grid-cols-[1.45fr_1fr]">
						<div class="space-y-5">
							<div class="space-y-3">
								<div class="flex flex-wrap items-center gap-2">
									<span
										class={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusClass(detail?.statut)}`}
									>
										{statusLabel(detail?.statut)}
									</span>
									<span
										class="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
									>
										Régime {detail?.regime_fiscal || 'IR'}
									</span>
								</div>
								<h2 class="text-3xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
									{detail?.nom || activeSci?.nom || 'SCI en cours de chargement'}
								</h2>
								<p class="max-w-3xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
									Fiche d’identité consolidée pour piloter la société, ses associés, ses actifs, les
									charges documentées et les mouvements de trésorerie.
								</p>
							</div>

							<div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
								<div
									class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
								>
									<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
										<Landmark class="h-4 w-4" />
										<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Société</p>
									</div>
									<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
										SIREN {detail?.siren || 'À compléter'}
									</p>
									<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
										{detail?.associes_count || 0} associé(s) rattaché(s)
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
										{detail?.user_role
											? mapAssociateRoleLabel(detail.user_role)
											: 'Rôle à confirmer'}
									</p>
									<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
										Part détenue {formatPercent(detail?.user_part, 'N/A')}
									</p>
								</div>

								<div
									class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
								>
									<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
										<Building2 class="h-4 w-4" />
										<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">
											Patrimoine
										</p>
									</div>
									<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
										{detail?.biens_count || 0} bien(s)
									</p>
									<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
										Loyer cible {formatEur(detail?.total_monthly_rent, 'N/A')}
									</p>
								</div>

								<div
									class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
								>
									<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
										<HandCoins class="h-4 w-4" />
										<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Charges</p>
									</div>
									<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
										{detail?.charges_count || 0} enregistrement(s)
									</p>
									<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
										Total documenté {formatEur(detail?.total_recorded_charges, 'N/A')}
									</p>
								</div>
							</div>
						</div>

						<div
							class="rounded-3xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-950"
						>
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
								Actions recommandées
							</p>
							<div class="mt-4 grid gap-2">
								<Button href="/dashboard" variant="outline" class="justify-start"
									>Ouvrir le cockpit</Button
								>
								<Button href="/biens" variant="outline" class="justify-start"
									>Gérer les biens</Button
								>
								<Button href="/loyers" variant="outline" class="justify-start"
									>Suivre les loyers</Button
								>
								<Button href="/settings" variant="outline" class="justify-start"
									>Paramètres de l'application</Button
								>
							</div>
							<div
								class="mt-6 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
							>
								<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
									<ShieldCheck class="h-4 w-4" />
									<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">
										Recouvrement
									</p>
								</div>
								<p class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">
									{formatPercent(collectionRate, '0%')}
								</p>
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
									Flux encaissés {formatEur(detail?.paid_loyers_total, 'N/A')} • en attente {formatEur(
										detail?.pending_loyers_total,
										'N/A'
									)}
								</p>
							</div>
						</div>
					</div>
				</CardContent>
			</Card>

			<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
				<KpiCard
					label="SCI suivies"
					value={formatCompactNumber(scis.length)}
					caption="entités actives dans le portefeuille"
					trend="up"
					trendValue="multi-SCI"
					tone="accent"
					{loading}
				/>
				<KpiCard
					label="Loyers encaissés"
					value={formatEur(detail?.paid_loyers_total, '—')}
					caption="flux sécurisés"
					trend="up"
					trendValue="trésorerie"
					tone="success"
					loading={detailLoading}
				/>
				<KpiCard
					label="Charges documentées"
					value={formatEur(detail?.total_recorded_charges, '—')}
					caption="pilotage des sorties"
					trend="neutral"
					trendValue="contrôle"
					tone="default"
					loading={detailLoading}
				/>
				<KpiCard
					label="Documents fiscaux"
					value={detail?.fiscalite?.length || 0}
					caption="années consolidées"
					trend="up"
					trendValue="traceabilité"
					tone="warning"
					loading={detailLoading}
				/>
			</div>

			<div class="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
				<Card class="sci-section-card">
					<CardHeader>
						<div>
							<CardTitle class="text-lg">Associés et gouvernance</CardTitle>
							<CardDescription
								>Répartition du capital, rôles et personnes impliquées dans la SCI sélectionnée.</CardDescription
							>
						</div>
					</CardHeader>
					<CardContent class="grid gap-3 pt-0 md:grid-cols-2">
						{#if detailLoading}
							{#each Array.from({ length: 2 }) as _}
								<div class="h-28 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
							{/each}
						{:else if detail?.associes?.length}
							{#each detail.associes as associe (String(associe.id))}
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
											{mapAssociateRoleLabel(associe.role)}
										</span>
									</div>
									<p
										class="mt-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
									>
										Part détenue
									</p>
									<p class="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
										{formatPercent(associe.part, 'N/A')}
									</p>
								</div>
							{/each}
						{:else}
							<p class="text-sm text-slate-500 dark:text-slate-400">
								Aucun associé détaillé n’est disponible pour cette SCI.
							</p>
						{/if}
					</CardContent>
				</Card>

				<Card class="sci-section-card">
					<CardHeader>
						<div>
							<CardTitle class="text-lg">Fiscalité et repères</CardTitle>
							<CardDescription
								>Dernières années consolidées et niveau de documentation disponible.</CardDescription
							>
						</div>
					</CardHeader>
					<CardContent class="space-y-3 pt-0">
						<div
							class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
						>
							<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
								<FileText class="h-4 w-4" />
								<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">
									Fiche fiscale
								</p>
							</div>
							<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
								{detail?.fiscalite?.length
									? `${detail.fiscalite.length} exercice(s) consolidé(s)`
									: 'Aucun exercice consolidé'}
							</p>
						</div>

						{#if detail?.fiscalite?.length}
							{#each detail.fiscalite as exercice (String(exercice.id || exercice.annee))}
								<div
									class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950"
								>
									<div class="flex items-center justify-between gap-3">
										<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
											Exercice {exercice.annee}
										</p>
										<span class="text-xs text-slate-500 dark:text-slate-400"
											>{formatEur(exercice.resultat_fiscal, 'N/A')}</span
										>
									</div>
									<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
										Revenus {formatEur(exercice.total_revenus, 'N/A')} • charges {formatEur(
											exercice.total_charges,
											'N/A'
										)}
									</p>
								</div>
							{/each}
						{:else}
							<p class="text-sm text-slate-500 dark:text-slate-400">
								Ajoute de la fiscalité consolidée pour alimenter les arbitrages de fin d’année.
							</p>
						{/if}
					</CardContent>
				</Card>
			</div>

			<div class="grid gap-6 xl:grid-cols-[1.35fr_1fr]">
				<Card class="sci-section-card">
					<CardHeader>
						<div>
							<CardTitle class="text-lg">Patrimoine rattaché</CardTitle>
							<CardDescription
								>Les biens de la SCI active, avec exposition locative et charges récurrentes.</CardDescription
							>
						</div>
					</CardHeader>
					<CardContent class="space-y-3 pt-0">
						{#if detailLoading}
							<div class="h-40 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
						{:else if detail?.biens?.length}
							<div class="grid gap-3 md:grid-cols-2">
								{#each detail.biens as bien (String(bien.id || `${bien.adresse}-${bien.ville}`))}
									<div
										class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
									>
										<div class="flex items-start justify-between gap-3">
											<div>
												<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
													{bien.adresse}
												</p>
												<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
													{bien.ville || 'Ville à compléter'} • {mapBienTypeLabel(
														bien.type_locatif
													)}
												</p>
											</div>
											<Building2 class="mt-0.5 h-4 w-4 text-slate-400" />
										</div>
										<div class="mt-4 grid grid-cols-2 gap-3 text-sm">
											<div>
												<p class="text-slate-500 dark:text-slate-400">Loyer CC</p>
												<p class="font-semibold text-slate-900 dark:text-slate-100">
													{formatEur(bien.loyer_cc, 'N/A')}
												</p>
											</div>
											<div>
												<p class="text-slate-500 dark:text-slate-400">Charges</p>
												<p class="font-semibold text-slate-900 dark:text-slate-100">
													{formatEur(bien.charges, 'N/A')}
												</p>
											</div>
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<p class="text-sm text-slate-500 dark:text-slate-400">
								Aucun bien n’est encore rattaché à cette SCI.
							</p>
						{/if}
					</CardContent>
				</Card>

				<Card class="sci-section-card">
					<CardHeader>
						<div>
							<CardTitle class="text-lg">Charges récentes</CardTitle>
							<CardDescription
								>Dernières sorties documentées sur les biens de la SCI.</CardDescription
							>
						</div>
					</CardHeader>
					<CardContent class="space-y-3 pt-0">
						{#if detailLoading}
							<div class="h-40 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
						{:else if detail?.recent_charges?.length}
							{#each detail.recent_charges as charge (String(charge.id || `${charge.id_bien}-${charge.date_paiement}`))}
								<div
									class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
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
							<p class="text-sm text-slate-500 dark:text-slate-400">
								Aucune charge documentée pour l’instant sur cette SCI.
							</p>
						{/if}
					</CardContent>
				</Card>
			</div>

			<Card class="sci-section-card">
				<CardHeader>
					<div>
						<CardTitle class="text-lg">Activité locative récente</CardTitle>
						<CardDescription
							>Historique synthétique des derniers loyers saisis, lisible sans identifiants
							techniques.</CardDescription
						>
					</div>
				</CardHeader>
				<CardContent class="grid gap-3 pt-0 md:grid-cols-2 xl:grid-cols-4">
					{#if detailLoading}
						{#each Array.from({ length: 4 }) as _}
							<div class="h-28 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
						{/each}
					{:else if detail?.recent_loyers?.length}
						{#each detail.recent_loyers as loyer (String(loyer.id || `${loyer.id_bien}-${loyer.date_loyer}`))}
							<div
								class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
							>
								<div class="flex items-center justify-between gap-3">
									<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
										{formatFrDate(loyer.date_loyer)}
									</p>
									<span
										class="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-semibold text-white dark:bg-slate-100 dark:text-slate-950"
									>
										{mapLoyerStatusLabel(loyer.statut)}
									</span>
								</div>
								<p class="mt-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
									{formatEur(loyer.montant, 'N/A')}
								</p>
								<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
									{bienLabel(loyer.id_bien)}
								</p>
							</div>
						{/each}
					{:else}
						<p class="text-sm text-slate-500 dark:text-slate-400">
							Aucun loyer documenté sur la période récente.
						</p>
					{/if}
				</CardContent>
			</Card>
		</div>
		</div>
	{/if}
</section>
