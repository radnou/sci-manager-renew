<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import AdminHeroKpis from '$lib/components/admin/AdminHeroKpis.svelte';
	import AdminAlerts from '$lib/components/admin/AdminAlerts.svelte';
	import AdminFunnel from '$lib/components/admin/AdminFunnel.svelte';

	type MetricValue = {
		value: number;
		previous: number;
		trend: string;
		change_pct: number | null;
	};
	type Metrics = {
		north_star: MetricValue;
		mrr: MetricValue;
		activation_rate: MetricValue;
		churn_30d: MetricValue;
		conversion_rate: MetricValue;
	};
	type Alerts = {
		alerts: Array<{
			type: string;
			severity: 'high' | 'medium' | 'info';
			message: string;
			detail: string;
			tooltip: string;
		}>;
	};
	type Funnel = {
		steps: Array<{ label: string; count: number; rate: number }>;
		bottleneck_index: number;
	};

	let metrics = $state<Metrics | null>(null);
	let alerts = $state<Alerts | null>(null);
	let funnel = $state<Funnel | null>(null);
	let loading = $state(true);
	let error = $state('');

	const adminKey = $derived(page.url.searchParams.get('secret') ?? '');

	async function adminFetch<T>(path: string): Promise<T> {
		const resp = await fetch(`${path}${path.includes('?') ? '&' : '?'}key=${encodeURIComponent(adminKey)}`);
		if (!resp.ok) throw new Error(`${resp.status}`);
		return resp.json();
	}

	onMount(async () => {
		if (!adminKey) return;
		try {
			const [m, a, f] = await Promise.all([
				adminFetch<Metrics>('/api/v1/admin/metrics'),
				adminFetch<Alerts>('/api/v1/admin/alerts'),
				adminFetch<Funnel>('/api/v1/admin/funnel')
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
	<title>Cockpit Business | Admin | GérerSCI</title>
</svelte:head>

{#if loading}
	<div class="flex items-center justify-center py-20">
		<div
			class="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-600"
		></div>
	</div>
{:else if error}
	<div
		class="rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 dark:border-rose-800 dark:bg-rose-950/30"
	>
		<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
	</div>
{:else}
	<div class="space-y-6">
		{#if metrics}
			<AdminHeroKpis {metrics} />
		{/if}

		{#if alerts}
			<div>
				<h2 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
					Alertes business
				</h2>
				<AdminAlerts alerts={alerts.alerts} />
			</div>
		{/if}

		{#if funnel}
			<AdminFunnel steps={funnel.steps} bottleneck_index={funnel.bottleneck_index} />
		{/if}
	</div>
{/if}
