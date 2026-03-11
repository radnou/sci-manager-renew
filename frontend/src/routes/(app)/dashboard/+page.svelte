<script lang="ts">
	import { Loader2 } from 'lucide-svelte';
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
		<p class="sci-eyebrow">Pilotage SCI</p>
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
