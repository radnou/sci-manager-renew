<script lang="ts">
	import { onMount } from 'svelte';
	import { apiFetch } from '$lib/api';

	let stats = $state<{
		total_users: number;
		total_scis: number;
		total_biens: number;
		active_subscriptions: number;
		plan_breakdown: Record<string, number>;
	} | null>(null);

	onMount(async () => {
		try {
			stats = await apiFetch('/api/v1/admin/stats');
		} catch {
			// handled by layout guard
		}
	});
</script>

<svelte:head>
	<title>Admin | GererSCI</title>
</svelte:head>

{#if stats}
	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		<div
			class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
		>
			<p class="text-xs font-semibold tracking-widest text-slate-500 uppercase">Utilisateurs</p>
			<p class="mt-2 text-3xl font-bold text-slate-900 dark:text-slate-100">{stats.total_users}</p>
		</div>
		<div
			class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
		>
			<p class="text-xs font-semibold tracking-widest text-slate-500 uppercase">SCI</p>
			<p class="mt-2 text-3xl font-bold text-slate-900 dark:text-slate-100">{stats.total_scis}</p>
		</div>
		<div
			class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
		>
			<p class="text-xs font-semibold tracking-widest text-slate-500 uppercase">Biens</p>
			<p class="mt-2 text-3xl font-bold text-slate-900 dark:text-slate-100">{stats.total_biens}</p>
		</div>
		<div
			class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
		>
			<p class="text-xs font-semibold tracking-widest text-slate-500 uppercase">
				Abonnements actifs
			</p>
			<p class="mt-2 text-3xl font-bold text-slate-900 dark:text-slate-100">
				{stats.active_subscriptions}
			</p>
		</div>
	</div>

	{#if Object.keys(stats.plan_breakdown).length > 0}
		<div
			class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
		>
			<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
				Répartition par plan
			</h2>
			<div class="mt-4 space-y-3">
				{#each Object.entries(stats.plan_breakdown) as [plan, count]}
					<div class="flex items-center justify-between">
						<span class="text-sm font-medium capitalize text-slate-700 dark:text-slate-300"
							>{plan}</span
						>
						<span
							class="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-900 dark:bg-slate-800 dark:text-slate-100"
							>{count}</span
						>
					</div>
				{/each}
			</div>
		</div>
	{/if}
{:else}
	<p class="text-sm text-slate-500">Chargement...</p>
{/if}
