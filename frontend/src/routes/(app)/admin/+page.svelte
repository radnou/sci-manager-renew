<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchAdminMetrics, fetchAdminAlerts, fetchAdminFunnel } from '$lib/api';
	import AdminHeroKpis from '$lib/components/admin/AdminHeroKpis.svelte';
	import AdminAlerts from '$lib/components/admin/AdminAlerts.svelte';
	import AdminFunnel from '$lib/components/admin/AdminFunnel.svelte';

	let metrics = $state<Awaited<ReturnType<typeof fetchAdminMetrics>> | null>(null);
	let alerts = $state<Awaited<ReturnType<typeof fetchAdminAlerts>> | null>(null);
	let funnel = $state<Awaited<ReturnType<typeof fetchAdminFunnel>> | null>(null);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			const [m, a, f] = await Promise.all([
				fetchAdminMetrics(),
				fetchAdminAlerts(),
				fetchAdminFunnel(),
			]);
			metrics = m;
			alerts = a;
			funnel = f;
		} catch (e) {
			error = 'Erreur lors du chargement des metriques';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Cockpit Business | Admin | GererSCI</title>
</svelte:head>

{#if loading}
	<div class="flex items-center justify-center py-20">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-600"></div>
	</div>
{:else if error}
	<div class="rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 dark:border-rose-800 dark:bg-rose-950/30">
		<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
	</div>
{:else}
	<div class="space-y-6">
		{#if metrics}
			<AdminHeroKpis {metrics} />
		{/if}

		{#if alerts}
			<div>
				<h2 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">Alertes business</h2>
				<AdminAlerts alerts={alerts.alerts} />
			</div>
		{/if}

		{#if funnel}
			<AdminFunnel steps={funnel.steps} bottleneck_index={funnel.bottleneck_index} />
		{/if}
	</div>
{/if}
