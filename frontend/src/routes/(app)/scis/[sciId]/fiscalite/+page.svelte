<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail, Fiscalite } from '$lib/api';
	import { fetchFiscalite, generateCerfa2044Pdf } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import { FileText, Calculator, Download } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');

	let exercices: Fiscalite[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);
	let generatingCerfa = $state(false);
	let cerfaError = $state('');

	$effect(() => {
		loadFiscalite();
	});

	async function loadFiscalite() {
		loading = true;
		error = null;
		try {
			exercices = await fetchFiscalite(sci.id);
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger la fiscalité.';
		} finally {
			loading = false;
		}
	}

	async function handleGenerateCerfa(exercice: Fiscalite) {
		generatingCerfa = true;
		cerfaError = '';
		try {
			const blob = await generateCerfa2044Pdf({
				annee: exercice.annee,
				total_revenus: exercice.total_revenus ?? 0,
				total_charges: exercice.total_charges ?? 0,
				sci_nom: sci.nom,
				siren: sci.siren ?? ''
			});
			const url = URL.createObjectURL(blob);
			window.open(url, '_blank');
		} catch (err: any) {
			cerfaError = err?.message ?? 'Erreur lors de la génération du CERFA.';
		} finally {
			generatingCerfa = false;
		}
	}

	function resultatColor(value: number | null | undefined): string {
		if (value == null) return 'text-slate-700 dark:text-slate-300';
		if (value > 0) return 'text-emerald-600 dark:text-emerald-400';
		if (value < 0) return 'text-rose-600 dark:text-rose-400';
		return 'text-slate-700 dark:text-slate-300';
	}
</script>

<svelte:head><title>Fiscalité | {sci.nom} | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<h1 class="sci-page-title">Fiscalité</h1>
	</header>

	<!-- Régime fiscal -->
	<div
		class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
	>
		<div class="flex items-center gap-2">
			<Calculator class="h-5 w-5 text-sky-600 dark:text-sky-400" />
			<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
				Régime fiscal
			</h2>
		</div>
		<div class="mt-4 grid gap-4 sm:grid-cols-2">
			<div>
				<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
					Régime
				</p>
				<p class="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">
					{#if sci.regime_fiscal === 'IR'}
						Impôt sur le Revenu (IR) — Revenus fonciers
					{:else if sci.regime_fiscal === 'IS'}
						Impôt sur les Sociétés (IS)
					{:else}
						{sci.regime_fiscal ?? 'Non renseigné'}
					{/if}
				</p>
			</div>
			<div>
				<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
					SCI
				</p>
				<p class="mt-1 text-sm text-slate-700 dark:text-slate-300">
					{sci.nom}
					{#if sci.siren}
						<span class="text-slate-400"> — SIREN {sci.siren}</span>
					{/if}
				</p>
			</div>
		</div>
	</div>

	<!-- CERFA 2044 Generation -->
	<div
		class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
	>
		<div class="flex items-center gap-2">
			<FileText class="h-5 w-5 text-sky-600 dark:text-sky-400" />
			<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
				Déclaration CERFA 2044
			</h2>
		</div>
		<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
			Générez un résumé simplifié de votre déclaration des revenus fonciers au format PDF.
		</p>

		{#if exercices.length > 0}
			<div class="mt-4 space-y-2">
				{#each exercices as ex (ex.id ?? ex.annee)}
					<div
						class="flex items-center justify-between rounded-lg border border-slate-100 px-4 py-3 dark:border-slate-800"
					>
						<div>
							<span class="font-semibold text-slate-900 dark:text-slate-100"
								>{ex.annee}</span
							>
							<span class="ml-3 text-sm text-slate-500">
								Revenus {formatEur(ex.total_revenus ?? 0)} — Charges {formatEur(
									ex.total_charges ?? 0
								)}
							</span>
						</div>
						<button
							class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
							disabled={generatingCerfa}
							onclick={() => handleGenerateCerfa(ex)}
						>
							<Download class="h-3.5 w-3.5" />
							{generatingCerfa ? 'Génération…' : 'CERFA 2044'}
						</button>
					</div>
				{/each}
			</div>
		{:else if !loading}
			<p class="mt-4 text-sm text-slate-500 dark:text-slate-400">
				Ajoutez un exercice fiscal pour pouvoir générer le CERFA 2044.
			</p>
		{/if}

		{#if cerfaError}
			<p class="mt-3 text-sm text-rose-600 dark:text-rose-400">{cerfaError}</p>
		{/if}
	</div>

	<!-- Exercices fiscaux -->
	<div
		class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
	>
		<div class="mb-4 flex items-center gap-2">
			<FileText class="h-5 w-5 text-sky-600 dark:text-sky-400" />
			<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
				Exercices fiscaux
			</h2>
		</div>

		{#if loading}
			<div class="space-y-3">
				{#each Array.from({ length: 3 }) as _}
					<div class="h-12 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-900"></div>
				{/each}
			</div>
		{:else if error}
			<div class="rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-900 dark:bg-rose-950/30">
				<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
				<button
					onclick={loadFiscalite}
					class="mt-2 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
				>
					Réessayer
				</button>
			</div>
		{:else if exercices.length === 0}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
			>
				<FileText class="mb-2 h-8 w-8 text-slate-300 dark:text-slate-600" />
				<p class="text-sm text-slate-500 dark:text-slate-400">
					Aucun exercice fiscal enregistré.
				</p>
			</div>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-slate-200 dark:border-slate-700">
							<th
								class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Année
							</th>
							<th
								class="pb-3 pr-4 text-right text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Revenus
							</th>
							<th
								class="pb-3 pr-4 text-right text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Charges
							</th>
							<th
								class="pb-3 text-right text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Résultat fiscal
							</th>
						</tr>
					</thead>
					<tbody>
						{#each exercices as ex (ex.id ?? ex.annee)}
							<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
								<td class="py-3 pr-4 font-semibold text-slate-900 dark:text-slate-100">
									{ex.annee}
								</td>
								<td class="py-3 pr-4 text-right text-emerald-700 dark:text-emerald-400">
									{formatEur(ex.total_revenus ?? 0)}
								</td>
								<td class="py-3 pr-4 text-right text-rose-700 dark:text-rose-400">
									{formatEur(ex.total_charges ?? 0)}
								</td>
								<td
									class="py-3 text-right font-semibold {resultatColor(ex.resultat_fiscal)}"
								>
									{formatEur(ex.resultat_fiscal ?? 0)}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</section>
