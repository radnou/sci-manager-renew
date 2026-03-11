<script lang="ts">
	import { page } from '$app/state';
	import { getContext } from 'svelte';
	import type { SCIDetail, FicheBien } from '$lib/api';
	import { fetchFicheBien } from '$lib/api';
	import FicheBienHeader from '$lib/components/fiche-bien/FicheBienHeader.svelte';
	import FicheBienIdentite from '$lib/components/fiche-bien/FicheBienIdentite.svelte';
	import FicheBienBail from '$lib/components/fiche-bien/FicheBienBail.svelte';
	import FicheBienLoyers from '$lib/components/fiche-bien/FicheBienLoyers.svelte';
	import FicheBienCharges from '$lib/components/fiche-bien/FicheBienCharges.svelte';

	const sci = getContext<SCIDetail>('sci');
	const userRole = getContext<string>('userRole');

	let sciId = $derived(page.params.sciId!);
	let bienId = $derived(page.params.bienId!);
	let isGerant = $derived(userRole === 'gerant');

	let bien: FicheBien | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);

	$effect(() => {
		if (sciId && bienId) {
			loadFicheBien();
		}
	});

	async function loadFicheBien() {
		loading = true;
		error = null;
		try {
			bien = await fetchFicheBien(sciId, bienId);
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger les données du bien.';
			bien = null;
		} finally {
			loading = false;
		}
	}
</script>

<section class="sci-page-shell">
	{#if loading}
		<div class="space-y-6">
			<div class="h-8 w-48 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-800"></div>
			<div class="h-6 w-64 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-800"></div>
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{#each Array.from({ length: 6 }) as _}
					<div class="h-20 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
				{/each}
			</div>
			<div class="h-48 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
		</div>
	{:else if error}
		<header class="sci-page-header">
			<p class="sci-eyebrow">{sci.nom} / Biens</p>
			<h1 class="sci-page-title">Erreur</h1>
		</header>
		<div class="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30">
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={loadFicheBien}
				class="mt-3 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				Réessayer
			</button>
		</div>
	{:else if bien}
		<FicheBienHeader {bien} sciNom={sci.nom} {isGerant} />

		<div class="mt-6 space-y-6">
			<FicheBienIdentite {bien} {isGerant} />
			<FicheBienBail bail={bien.bail_actif} {isGerant} sciId={sciId} bienId={String(bien.id)} />
			<FicheBienLoyers loyers={bien.loyers_recents} {isGerant} {sciId} {bienId} />
			<FicheBienCharges
				charges={bien.charges_list}
				assurancePno={bien.assurance_pno}
				fraisAgence={bien.frais_agence}
				{isGerant}
				sciId={sciId}
				bienId={String(bien.id)}
			/>
		</div>
	{/if}
</section>
