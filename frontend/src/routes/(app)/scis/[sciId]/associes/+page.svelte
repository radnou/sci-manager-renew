<script lang="ts">
	import { page } from '$app/state';
	import { getContext } from 'svelte';
	import type { SCIDetail, Associe } from '$lib/api';
	import { fetchSciAssociesList } from '$lib/api';
	import RoleGate from '$lib/components/RoleGate.svelte';
	import { UserPlus } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');
	const userRole = getContext<string>('userRole');

	let sciId = $derived(page.params.sciId!);
	let isGerant = $derived(userRole === 'gerant');

	let associes: Associe[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);

	$effect(() => {
		if (sciId) {
			loadAssocies();
		}
	});

	async function loadAssocies() {
		loading = true;
		error = null;
		try {
			associes = await fetchSciAssociesList(sciId);
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger les associés.';
			associes = [];
		} finally {
			loading = false;
		}
	}

	const roleBadge: Record<string, { label: string; class: string }> = {
		gerant: {
			label: 'Gérant',
			class: 'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300'
		},
		associe: {
			label: 'Associé',
			class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
		}
	};

	function getRoleBadge(role: string | null | undefined) {
		if (!role) return roleBadge['associe'];
		return roleBadge[role] ?? roleBadge['associe'];
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<div class="flex items-center justify-between">
			<h1 class="sci-page-title">Associés</h1>
			{#if isGerant}
				<button
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				>
					<UserPlus class="h-4 w-4" />
					Inviter un associé
				</button>
			{/if}
		</div>
	</header>

	{#if loading}
		<div class="space-y-3">
			{#each Array.from({ length: 3 }) as _}
				<div
					class="h-16 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-900"
				></div>
			{/each}
		</div>
	{:else if error}
		<div
			class="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30"
		>
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={loadAssocies}
				class="mt-3 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				Réessayer
			</button>
		</div>
	{:else if associes.length > 0}
		<div class="space-y-3">
			{#each associes as associe (String(associe.id))}
				<div
					class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950"
				>
					<div class="flex items-center justify-between">
						<div>
							<p class="font-medium text-slate-900 dark:text-slate-100">
								{associe.nom}
							</p>
							{#if associe.email}
								<p class="text-sm text-slate-500 dark:text-slate-400">
									{associe.email}
								</p>
							{/if}
						</div>
						<div class="flex items-center gap-2">
							<span
								class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {getRoleBadge(associe.role).class}"
							>
								{getRoleBadge(associe.role).label}
							</span>
							<span
								class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300"
							>
								{associe.part ?? 0}%
							</span>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<div
			class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
		>
			<p class="text-sm text-slate-500 dark:text-slate-400">Aucun associé.</p>
			{#if isGerant}
				<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
					Cliquez sur "Inviter un associé" pour ajouter un membre.
				</p>
			{/if}
		</div>
	{/if}
</section>
