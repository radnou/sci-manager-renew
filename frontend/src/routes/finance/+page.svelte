<script lang="ts">
	import { onMount } from 'svelte';
	import {
		fetchCharges,
		fetchFiscalite,
		fetchLoyers,
		fetchScis,
		type Charge,
		type Fiscalite,
		type Loyer,
		type SCIOverview
	} from '$lib/api';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import GettingStartedPanel from '$lib/components/GettingStartedPanel.svelte';
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import PageSpecificSkeleton from '$lib/components/PageSpecificSkeleton.svelte';
	import WorkspaceActionBar from '$lib/components/WorkspaceActionBar.svelte';
	import WorkspaceHeader from '$lib/components/WorkspaceHeader.svelte';
	import WorkspaceRailCard from '$lib/components/WorkspaceRailCard.svelte';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { formatCompactNumber, formatEur } from '$lib/high-value/formatters';
	import { calculateChargeMetrics } from '$lib/high-value/charges';
	import { calculateFiscaliteMetrics } from '$lib/high-value/fiscalite';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { getStoredActiveSciId, setStoredActiveSciId } from '$lib/portfolio/active-sci';

	let scis: SCIOverview[] = [];
	let charges: Charge[] = [];
	let fiscalite: Fiscalite[] = [];
	let loyers: Loyer[] = [];
	let loading = true;
	let errorMessage = '';
	let activeSciId = '';

	$: resolvedActiveSciId =
		activeSciId && scis.some((sci) => String(sci.id) === activeSciId)
			? activeSciId
			: String(scis[0]?.id || '');
	$: activeSci = scis.find((sci) => String(sci.id) === resolvedActiveSciId) ?? null;
	$: scopedCharges = activeSci
		? charges.filter((charge) => String(charge.id_sci || '') === String(activeSci.id))
		: charges;
	$: scopedFiscalite = activeSci
		? fiscalite.filter((entry) => String(entry.id_sci || '') === String(activeSci.id))
		: fiscalite;
	$: scopedLoyers = activeSci
		? loyers.filter((loyer) => String(loyer.id_sci || '') === String(activeSci.id))
		: loyers;
	$: chargeMetrics = calculateChargeMetrics(scopedCharges);
	$: fiscaliteMetrics = calculateFiscaliteMetrics(scopedFiscalite);
	$: if (resolvedActiveSciId) {
		setStoredActiveSciId(resolvedActiveSciId);
	}
	$: shouldShowOnboarding =
		!loading && (scopedCharges.length === 0 || scopedFiscalite.length === 0);

	onMount(loadOverview);

	async function loadOverview() {
		loading = true;
		errorMessage = '';

		try {
			const [nextScis, nextCharges, nextFiscalite, nextLoyers] = await Promise.all([
				fetchScis(),
				fetchCharges(),
				fetchFiscalite(),
				fetchLoyers()
			]);
			scis = Array.isArray(nextScis) ? nextScis : [];
			charges = Array.isArray(nextCharges) ? nextCharges : [];
			fiscalite = Array.isArray(nextFiscalite) ? nextFiscalite : [];
			loyers = Array.isArray(nextLoyers) ? nextLoyers : [];
			const storedActiveSciId = getStoredActiveSciId();
			activeSciId =
				(storedActiveSciId &&
					nextScis.some((sci) => String(sci.id) === storedActiveSciId) &&
					storedActiveSciId) ||
				String(nextScis[0]?.id || '');
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, "Impossible de charger l'espace Finance.");
		} finally {
			loading = false;
		}
	}
</script>

<section class="sci-page-shell">
	<WorkspaceHeader
		eyebrow="Finance • sorties, clôture, documents"
		title="Hub finance"
		subtitle="Le point d’entrée financier de la SCI active: journal des charges, exercices fiscaux et accès aux documents produits à partir des flux locatifs."
		contextLabel="SCI active"
		contextValue={activeSci?.nom || 'Aucune SCI sélectionnée'}
		contextDetail={activeSci
			? `${scopedCharges.length} charge(s), ${scopedFiscalite.length} exercice(s), ${scopedLoyers.length} loyer(s) utilisables pour les documents.`
			: 'Choisis une SCI dans le portefeuille pour cadrer ce hub.'}
	>
		{#if scis.length > 0}
			<label class="sci-field min-w-[14rem]">
				<span class="sci-field-label">SCI active</span>
				<select bind:value={activeSciId} class="sci-select" aria-label="SCI active">
					{#each scis as sci (sci.id)}
						<option value={String(sci.id || '')}>{sci.nom}</option>
					{/each}
				</select>
			</label>
		{/if}
		<Button href="/charges">Documenter une charge</Button>
		<Button href="/fiscalite" variant="outline">Ouvrir la fiscalité</Button>
		<Button href="/account" variant="outline">Ouvrir le compte</Button>
	</WorkspaceHeader>

	{#if errorMessage}
		<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
	{/if}

	{#if loading}
		<PageSpecificSkeleton
			mode="hub"
			eyebrow="Chargement finance"
			title="Préparation du hub Finance"
			description="On aligne les sorties, les exercices fiscaux et les flux exploitables pour les documents."
		/>
	{:else if scis.length === 0}
		<EmptyState
			align="left"
			eyebrow="Aucune SCI exploitable"
			title="La finance ne démarre qu’une fois la SCI et le patrimoine en place"
			description="Crée d’abord la société et son socle d’exploitation avant d’ouvrir les journaux de charges et la fiscalité."
			actions={[
				{ label: 'Créer ma première SCI', href: '/scis' },
				{ label: 'Retour au cockpit', href: '/dashboard', variant: 'outline' }
			]}
		/>
	{:else}
		{#if shouldShowOnboarding}
			<div class="mb-6">
				<GettingStartedPanel
					compact={true}
					scope="finance"
					sciCount={scis.length}
					chargeCount={scopedCharges.length}
					fiscaliteCount={scopedFiscalite.length}
					activeSciLabel={activeSci?.nom || ''}
				/>
			</div>
		{/if}

		<WorkspaceActionBar
			eyebrow="Cadre financier"
			title="Journaux d’abord, consolidation ensuite"
			description="La lecture financière commence par les charges réellement payées, puis remonte vers la clôture et les documents produits à partir des flux."
		>
			<div class="sci-action-grid">
				<div class="sci-action-card">
					<p class="sci-action-card-title">Sorties réelles</p>
					<p class="sci-action-card-value">{chargeMetrics.totalLabel}</p>
					<p class="sci-action-card-body">
						{scopedCharges.length} charge(s) documentée(s) dans la SCI active.
					</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Clôture</p>
					<p class="sci-action-card-value">
						{scopedFiscalite.length > 0
							? `${scopedFiscalite.length} exercice(s)`
							: 'Aucun exercice'}
					</p>
					<p class="sci-action-card-body">
						La fiscalité consolide revenus et charges pour alimenter la lecture annuelle.
					</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Documents</p>
					<p class="sci-action-card-value">
						{scopedLoyers.length > 0 ? 'Quittances disponibles' : 'Flux locatifs requis'}
					</p>
					<p class="sci-action-card-body">
						Les PDF s’appuient sur les loyers saisis. Ils restent secondaires face aux journaux.
					</p>
				</div>
			</div>
			<div class="sci-primary-actions mt-5">
				<Button href="/charges">Gérer les charges</Button>
				<Button href="/fiscalite" variant="outline">Gérer la fiscalité</Button>
				<Button href="/loyers" variant="outline">Ouvrir les quittances PDF</Button>
			</div>
			{#snippet aside()}
				<WorkspaceRailCard
					title="Vision"
					description="La finance devient vraiment utile quand les charges sont documentées et qu’un premier exercice existe."
				>
					<div class="space-y-3">
						<div class="sci-action-card">
							<p class="sci-action-card-title">Maintenant</p>
							<p class="sci-action-card-value">
								{scopedCharges.length === 0
									? 'Documenter la première charge'
									: scopedFiscalite.length === 0
										? 'Ouvrir le premier exercice'
										: 'Contrôler la clôture en cours'}
							</p>
						</div>
						<div class="grid gap-2">
							<Button href="/dashboard" variant="outline" class="w-full justify-start">
								Revenir au cockpit
							</Button>
							<Button href="/account" variant="outline" class="w-full justify-start">
								Voir le compte
							</Button>
						</div>
					</div>
				</WorkspaceRailCard>
			{/snippet}
		</WorkspaceActionBar>

		<div class="grid gap-6 xl:grid-cols-3">
			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="text-lg">Charges</CardTitle>
					<CardDescription
						>Le journal des décaissements réels reste la lecture financière la plus fréquente.</CardDescription
					>
				</CardHeader>
				<CardContent class="space-y-4 pt-0">
					<KpiCard
						label="Sorties documentées"
						value={formatCompactNumber(scopedCharges.length)}
						caption={chargeMetrics.totalLabel}
						trend={scopedCharges.length > 0 ? 'up' : 'neutral'}
						trendValue={scopedCharges.length > 0 ? 'journal actif' : 'à ouvrir'}
						tone={scopedCharges.length > 0 ? 'accent' : 'default'}
					/>
					<p class="text-sm leading-relaxed text-slate-500 dark:text-slate-400">
						Filtre ensuite par bien, type de charge et période pour passer du volume brut au
						contrôle opérationnel.
					</p>
					<div class="flex flex-wrap gap-2">
						<Button href="/charges">Ouvrir Charges</Button>
						<Button href="/charges" variant="outline">Ajouter une charge</Button>
					</div>
				</CardContent>
			</Card>

			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="text-lg">Fiscalité</CardTitle>
					<CardDescription
						>Les exercices consolidés servent à comparer l’annuel, pas à piloter le quotidien.</CardDescription
					>
				</CardHeader>
				<CardContent class="space-y-4 pt-0">
					<KpiCard
						label="Exercices ouverts"
						value={formatCompactNumber(scopedFiscalite.length)}
						caption={fiscaliteMetrics.latestYear == null
							? 'aucune année'
							: `dernier exercice ${fiscaliteMetrics.latestYear}`}
						trend={scopedFiscalite.length > 0 ? 'up' : 'neutral'}
						trendValue={scopedFiscalite.length > 0 ? 'consolidation' : 'à préparer'}
						tone={scopedFiscalite.length > 0 ? 'warning' : 'default'}
					/>
					<p class="text-sm leading-relaxed text-slate-500 dark:text-slate-400">
						Revenus, charges et résultat fiscal sont cadrés ici pour la lecture annuelle de la SCI.
					</p>
					<div class="flex flex-wrap gap-2">
						<Button href="/fiscalite">Ouvrir la fiscalité</Button>
						<Button href="/fiscalite" variant="outline">Créer un exercice</Button>
					</div>
				</CardContent>
			</Card>

			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle class="text-lg">Documents</CardTitle>
					<CardDescription
						>Les quittances et PDF ne sont pas un module autonome: ils servent les flux locatifs
						déjà saisis.</CardDescription
					>
				</CardHeader>
				<CardContent class="space-y-4 pt-0">
					<KpiCard
						label="Flux documentables"
						value={formatCompactNumber(scopedLoyers.length)}
						caption="loyers disponibles pour les PDF"
						trend={scopedLoyers.length > 0 ? 'up' : 'neutral'}
						trendValue={scopedLoyers.length > 0 ? 'prêt' : 'en attente'}
						tone={scopedLoyers.length > 0 ? 'success' : 'default'}
					/>
					<p class="text-sm leading-relaxed text-slate-500 dark:text-slate-400">
						Les documents sont activés à partir du journal de loyers. Le point d’entrée reste donc
						le module Loyers.
					</p>
					<div class="flex flex-wrap gap-2">
						<Button href="/loyers">Ouvrir Loyers</Button>
						<Button href="/account" variant="outline">Ouvrir le compte</Button>
					</div>
				</CardContent>
			</Card>
		</div>
	{/if}
</section>
