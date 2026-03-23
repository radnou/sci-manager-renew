<script lang="ts">
	import { onMount } from 'svelte';
	import { adminKey } from '$lib/stores/admin-auth';
	import AdminRevenueBreakdown from '$lib/components/admin/AdminRevenueBreakdown.svelte';
	import AdminCohortTable from '$lib/components/admin/AdminCohortTable.svelte';

	let revenueData = $state<any>(null);
	let cohortData = $state<any>(null);
	let loading = $state(true);
	let error = $state('');

	async function adminFetch<T>(path: string): Promise<T> {
		const resp = await fetch(path, { headers: { 'X-Admin-Key': $adminKey } });
		if (!resp.ok) throw new Error(`${resp.status}`);
		return resp.json();
	}

	onMount(async () => {
		if (!$adminKey) return;
		try {
			const [rev, coh] = await Promise.all([
				adminFetch('/api/v1/admin/revenue'),
				adminFetch('/api/v1/admin/cohorts')
			]);
			// Normalize API response to match component props
			const totalSubs = (rev as any).breakdown?.reduce(
				(s: number, p: any) => s + (p.subscribers || p.count || 0),
				0
			);
			revenueData = {
				total_mrr: (rev as any).total_mrr || 0,
				arpu: totalSubs > 0 ? (rev as any).total_mrr / totalSubs : 0,
				breakdown: ((rev as any).breakdown || []).map((p: any) => ({
					plan: p.plan,
					count: p.subscribers ?? p.count ?? 0,
					mrr: p.mrr ?? 0,
					percentage: p.pct_of_total ?? p.percentage ?? 0
				}))
			};
			cohortData = coh;
		} catch {
			error = 'Erreur lors du chargement';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Revenue & Cohortes | Admin | GérerSCI</title>
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
		<p class="text-rose-700 dark:text-rose-400">{error}</p>
	</div>
{:else}
	<div class="space-y-6">
		{#if revenueData}
			<AdminRevenueBreakdown data={revenueData} />
		{/if}
		{#if cohortData}
			<AdminCohortTable data={cohortData} />
		{/if}
	</div>
{/if}
