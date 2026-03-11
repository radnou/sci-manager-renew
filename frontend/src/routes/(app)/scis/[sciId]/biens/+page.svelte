<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';
	import { fetchSciBiensList } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import { MapPin, Plus } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');
	const sciId = getContext<string>('sciId');
	const userRole = getContext<string>('userRole');

	let isGerant = $derived(userRole === 'gerant');

	let biens: Array<any> = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);

	$effect(() => {
		loadBiens();
	});

	async function loadBiens() {
		loading = true;
		error = null;
		try {
			biens = await fetchSciBiensList(sciId);
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger la liste des biens.';
			biens = [];
		} finally {
			loading = false;
		}
	}

	const statutBadge: Record<string, string> = {
		loue: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
		vacant: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
		travaux: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
	};
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<div class="flex items-center justify-between">
			<h1 class="sci-page-title">Biens</h1>
			{#if isGerant}
				<button
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				>
					<Plus class="h-4 w-4" />
					Ajouter un bien
				</button>
			{/if}
		</div>
	</header>

	{#if loading}
		<div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each Array.from({ length: 3 }) as _}
				<div class="h-40 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
			{/each}
		</div>
	{:else if error}
		<div class="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30">
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={loadBiens}
				class="mt-3 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				Réessayer
			</button>
		</div>
	{:else if biens.length === 0}
		<div class="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-16 dark:border-slate-700">
			<MapPin class="mb-3 h-10 w-10 text-slate-300 dark:text-slate-600" />
			<p class="text-sm font-medium text-slate-600 dark:text-slate-400">Aucun bien enregistré</p>
			<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
				{#if isGerant}
					Cliquez sur "Ajouter un bien" pour commencer.
				{:else}
					Le gérant n'a pas encore ajouté de bien.
				{/if}
			</p>
		</div>
	{:else}
		<div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each biens as bien (bien.id)}
				{@const statut = bien.statut ?? 'vacant'}
				{@const badgeClass = statutBadge[statut] ?? statutBadge['vacant']}
				<a
					href="/scis/{sciId}/biens/{bien.id}"
					class="group rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700"
				>
					<div class="flex items-start justify-between">
						<h3 class="font-semibold text-slate-900 group-hover:text-sky-600 dark:text-slate-100 dark:group-hover:text-sky-400">
							{bien.adresse}
						</h3>
						<span class="inline-flex items-center rounded-full px-2 py-0.5 text-[0.65rem] font-medium {badgeClass}">
							{statut}
						</span>
					</div>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						{bien.ville ?? ''} {bien.code_postal ?? ''}
					</p>
					<div class="mt-4 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
						{#if bien.type_bien ?? bien.type_locatif}
							<span class="rounded-full bg-slate-100 px-2 py-0.5 dark:bg-slate-800">
								{bien.type_bien ?? bien.type_locatif}
							</span>
						{/if}
						{#if bien.loyer ?? bien.loyer_cc}
							<span class="font-medium text-slate-700 dark:text-slate-300">
								{formatEur(bien.loyer ?? bien.loyer_cc)}/mois
							</span>
						{/if}
					</div>
				</a>
			{/each}
		</div>
	{/if}
</section>
