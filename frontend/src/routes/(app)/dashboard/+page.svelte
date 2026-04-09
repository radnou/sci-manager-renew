<script lang="ts">
	import { Rocket, Building2, HandCoins, FileText, CheckCircle2, ArrowRight } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import {
		fetchDashboard,
		type DashboardData,
		type DashboardAlerte,
		type DashboardKpis,
		type SCICard,
		type ActivityItem
	} from '$lib/api';
	import DashboardAlerts from '$lib/components/dashboard/DashboardAlerts.svelte';
	import DashboardKpisComponent from '$lib/components/dashboard/DashboardKpis.svelte';
	import DashboardSciCards from '$lib/components/dashboard/DashboardSciCards.svelte';
	import DashboardActivity from '$lib/components/dashboard/DashboardActivity.svelte';
	import AnneeSelector from '$lib/components/AnneeSelector.svelte';
	import OnboardingTour from '$lib/components/OnboardingTour.svelte';
	import Celebration from '$lib/components/Celebration.svelte';

	const upgraded = $derived(page.url.searchParams.get('upgraded') === 'true');

	// Auto-redirect to onboarding after checkout celebration
	$effect(() => {
		if (upgraded && !loading) {
			const timer = setTimeout(() => {
				goto('/onboarding');
			}, 4000);
			return () => clearTimeout(timer);
		}
	});

	const currentYear = new Date().getFullYear();
	let selectedYear = $state(currentYear);

	let loading = $state(true);
	let errorMessage = $state('');
	let showCelebration = $state(false);

	let alertes = $state<DashboardAlerte[]>([]);
	let kpis = $state<DashboardKpis>({
		sci_count: 0,
		biens_count: 0,
		taux_recouvrement: 0,
		cashflow_net: 0
	});
	let previousKpis = $state<DashboardKpis | null>(null);
	let scis = $state<SCICard[]>([]);
	let activite = $state<ActivityItem[]>([]);

	const isBrandNew = $derived(
		scis.length === 0 && activite.length === 0 && alertes.length === 0 && kpis.sci_count === 0
	);

	$effect(() => {
		loadDashboard(selectedYear);
	});

	async function loadDashboard(annee: number) {
		loading = true;
		errorMessage = '';
		try {
			const [data, prevData] = await Promise.all([
				fetchDashboard(annee),
				fetchDashboard(annee - 1).catch(() => null)
			]);
			alertes = data.alertes ?? [];
			kpis = data.kpis ?? { sci_count: 0, biens_count: 0, taux_recouvrement: 0, cashflow_net: 0 };
			scis = data.scis ?? [];
			activite = data.activite ?? [];
			previousKpis = prevData?.kpis ?? null;

			// Milestone 3: Dashboard Complete celebration (delayed to avoid overlap with onboarding tour)
			if (kpis.sci_count >= 1 && kpis.biens_count >= 1 && (kpis.taux_recouvrement > 0 || kpis.cashflow_net !== 0)) {
				if (!localStorage.getItem('milestone_dashboard_complete')) {
					localStorage.setItem('milestone_dashboard_complete', 'true');
					// Delay 3s so the onboarding tour modal is visible first
					setTimeout(() => { showCelebration = true; }, 3000);
				}
			}
		} catch (err) {
			const message =
				err instanceof Error ? err.message : 'Impossible de charger le tableau de bord.';
			errorMessage = message;
		} finally {
			loading = false;
		}
	}

	function computeVariation(current: number, previous: number | undefined | null): { text: string; color: string } | null {
		if (previous == null || previous === 0) return null;
		const pct = Math.round(((current - previous) / Math.abs(previous)) * 100);
		if (pct === 0) return null;
		return {
			text: pct > 0 ? `+${pct}%` : `${pct}%`,
			color: pct > 0 ? 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/40' : 'text-rose-600 bg-rose-50 dark:text-rose-400 dark:bg-rose-950/40'
		};
	}

	function handleYearChange(year: number) {
		selectedYear = year;
	}

	const kpiVariations = $derived(
		previousKpis
			? [
					{ label: 'Recouvrement', v: computeVariation(kpis.taux_recouvrement, previousKpis.taux_recouvrement) },
					{ label: 'Cashflow', v: computeVariation(kpis.cashflow_net, previousKpis.cashflow_net) }
				].filter(item => item.v != null)
			: []
	);
</script>

<svelte:head><title>Cockpit | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Gestion SCI</p>
		<div class="flex items-center gap-3">
			<h1 class="sci-page-title">Dashboard</h1>
			<AnneeSelector value={selectedYear} onchange={handleYearChange} />
		</div>
	</header>

	{#if upgraded}
		<div class="mt-6 flex flex-col items-center justify-center rounded-2xl border border-emerald-200 bg-emerald-50 px-6 py-10 text-center dark:border-emerald-800 dark:bg-emerald-950/30">
			<div class="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/50">
				<CheckCircle2 class="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
			</div>
			<h2 class="mt-4 text-lg font-semibold text-emerald-800 dark:text-emerald-200">
				Abonnement activé !
			</h2>
			<p class="mt-2 max-w-md text-sm text-emerald-700 dark:text-emerald-300">
				Vos données de démonstration ont été nettoyées. Créez maintenant votre première SCI avec vos vraies informations.
			</p>
			<a href="/onboarding" class="mt-6 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-700">
				Commencer la mise en route
				<ArrowRight class="h-4 w-4" />
			</a>
		</div>
	{/if}

	{#if loading}
		<div class="sci-loading" aria-label="Chargement"></div>
	{:else if errorMessage}
		<div
			class="rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 dark:border-rose-800 dark:bg-rose-950/30"
		>
			<p class="text-sm font-medium text-rose-700 dark:text-rose-300">{errorMessage}</p>
			<button
				type="button"
				class="mt-2 text-sm font-semibold text-rose-600 underline underline-offset-2 hover:no-underline dark:text-rose-400"
				onclick={() => loadDashboard(selectedYear)}
			>
				Réessayer
			</button>
		</div>
	{:else if isBrandNew}
		<!-- Welcome state for brand new users -->
		<div class="mt-8 flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-16 text-center dark:border-slate-700 dark:bg-slate-900">
			<div class="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-950/40">
				<Rocket class="h-7 w-7 text-indigo-500 dark:text-indigo-400" />
			</div>
			<h2 class="mt-5 text-lg font-semibold text-slate-900 dark:text-slate-100">
				Bienvenue sur GérerSCI
			</h2>
			<p class="mt-2 max-w-md text-sm text-slate-500 dark:text-slate-400">
				Votre tableau de bord prendra vie dès votre première SCI. En quelques minutes, suivez vos biens, loyers et charges depuis une interface consolidée.
			</p>

			<div class="mt-8 grid w-full max-w-lg gap-4 sm:grid-cols-3">
				<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
					<Building2 class="mx-auto h-6 w-6 text-sky-500" />
					<p class="mt-2 text-xs font-semibold text-slate-700 dark:text-slate-300">1. Créez une SCI</p>
					<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">Identité, SIREN, régime fiscal</p>
				</div>
				<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
					<HandCoins class="mx-auto h-6 w-6 text-emerald-500" />
					<p class="mt-2 text-xs font-semibold text-slate-700 dark:text-slate-300">2. Ajoutez un bien</p>
					<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">Adresse, bail, locataire</p>
				</div>
				<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
					<FileText class="mx-auto h-6 w-6 text-violet-500" />
					<p class="mt-2 text-xs font-semibold text-slate-700 dark:text-slate-300">3. Suivez vos loyers</p>
					<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">Encaissements, quittances</p>
				</div>
			</div>

			<a href="/onboarding" class="mt-8">
				<Button size="lg">Commencer la mise en route</Button>
			</a>
		</div>
	{:else}
		<div class="sci-stagger">
			<!-- Alertes -->
			<div class="mt-6">
				<DashboardAlerts {alertes} />
			</div>

			<!-- KPIs with N-1 variation -->
			<div class="mt-6">
				<DashboardKpisComponent {kpis} />
				{#if kpiVariations.length > 0}
					<div class="mt-2 flex flex-wrap gap-3">
						{#each kpiVariations as item}
							{#if item.v}
								<span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold {item.v.color}">
									{item.label} vs N-1 : {item.v.text}
								</span>
							{/if}
						{/each}
					</div>
				{/if}
			</div>

			<!-- SCI Cards -->
			<div class="mt-8">
				<h2 class="mb-4 text-sm font-semibold tracking-wider text-slate-500 uppercase dark:text-slate-400">
					Mes SCI
				</h2>
				<DashboardSciCards {scis} />
			</div>

			<!-- Activité récente -->
			<div class="mt-8">
				<DashboardActivity {activite} />
			</div>
		</div>
	{/if}
</section>

<OnboardingTour />

{#if showCelebration}
	<Celebration
		type="confetti"
		title="Votre SCI est 100% opérationnelle"
		subtitle="Loyers, quittances, fiscalité — tout est en place. GérerSCI travaille pour vous."
		onDismiss={() => { showCelebration = false; }}
	/>
{/if}
