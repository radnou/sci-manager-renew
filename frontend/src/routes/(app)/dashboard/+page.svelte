<script lang="ts">
	import { Loader2, Rocket, Building2, HandCoins, FileText } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
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

	let loading = $state(true);
	let errorMessage = $state('');

	let alertes = $state<DashboardAlerte[]>([]);
	let kpis = $state<DashboardKpis>({
		sci_count: 0,
		biens_count: 0,
		taux_recouvrement: 0,
		cashflow_net: 0
	});
	let scis = $state<SCICard[]>([]);
	let activite = $state<ActivityItem[]>([]);

	const isBrandNew = $derived(
		scis.length === 0 && activite.length === 0 && alertes.length === 0 && kpis.sci_count === 0
	);

	$effect(() => {
		loadDashboard();
	});

	async function loadDashboard() {
		loading = true;
		errorMessage = '';
		try {
			const data: DashboardData = await fetchDashboard();
			alertes = data.alertes ?? [];
			kpis = data.kpis ?? { sci_count: 0, biens_count: 0, taux_recouvrement: 0, cashflow_net: 0 };
			scis = data.scis ?? [];
			activite = data.activite ?? [];
		} catch (err) {
			const message =
				err instanceof Error ? err.message : 'Impossible de charger le tableau de bord.';
			errorMessage = message;
		} finally {
			loading = false;
		}
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Gestion SCI</p>
		<h1 class="sci-page-title">Dashboard</h1>
	</header>

	{#if loading}
		<div class="flex items-center justify-center py-24">
			<Loader2 class="h-8 w-8 animate-spin text-slate-400" />
			<span class="ml-3 text-sm text-slate-500 dark:text-slate-400">Chargement du tableau de bord...</span>
		</div>
	{:else if errorMessage}
		<div
			class="rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 dark:border-rose-800 dark:bg-rose-950/30"
		>
			<p class="text-sm font-medium text-rose-700 dark:text-rose-300">{errorMessage}</p>
			<button
				type="button"
				class="mt-2 text-sm font-semibold text-rose-600 underline underline-offset-2 hover:no-underline dark:text-rose-400"
				onclick={loadDashboard}
			>
				Reessayer
			</button>
		</div>
	{:else if isBrandNew}
		<!-- Welcome state for brand new users -->
		<div class="mt-8 flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-16 text-center dark:border-slate-700 dark:bg-slate-900">
			<div class="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-950/40">
				<Rocket class="h-7 w-7 text-indigo-500 dark:text-indigo-400" />
			</div>
			<h2 class="mt-5 text-lg font-semibold text-slate-900 dark:text-slate-100">
				Bienvenue sur GererSCI
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
		<!-- Alertes -->
		<div class="mt-6">
			<DashboardAlerts {alertes} />
		</div>

		<!-- KPIs -->
		<div class="mt-6">
			<DashboardKpisComponent {kpis} />
		</div>

		<!-- SCI Cards -->
		<div class="mt-8">
			<h2 class="mb-4 text-sm font-semibold tracking-wider text-slate-500 uppercase dark:text-slate-400">
				Mes SCI
			</h2>
			<DashboardSciCards {scis} />
		</div>

		<!-- Activite recente -->
		<div class="mt-8">
			<DashboardActivity {activite} />
		</div>
	{/if}
</section>
