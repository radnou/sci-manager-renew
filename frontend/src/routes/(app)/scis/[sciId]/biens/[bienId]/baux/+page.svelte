<script lang="ts">
	import { page } from '$app/state';
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';
	import { fetchBienBaux } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { ArrowLeft, Users, Calendar } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');
	const userRole = getContext<string>('userRole');

	let sciId = $derived(page.params.sciId!);
	let bienId = $derived(page.params.bienId!);

	let baux: any[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);

	$effect(() => {
		if (sciId && bienId) {
			loadBaux();
		}
	});

	async function loadBaux() {
		loading = true;
		error = null;
		try {
			baux = await fetchBienBaux(sciId, bienId);
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger les baux.';
			baux = [];
		} finally {
			loading = false;
		}
	}

	const statutConfig: Record<string, { label: string; class: string }> = {
		en_cours: {
			label: 'En cours',
			class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
		},
		expire: {
			label: 'Expiré',
			class: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
		},
		resilie: {
			label: 'Résilié',
			class: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
		}
	};

	function getStatut(statut: string | null | undefined) {
		if (!statut) return statutConfig['en_cours'];
		return (
			statutConfig[statut] ?? {
				label: statut,
				class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
			}
		);
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom} / Biens / Baux</p>
		<div class="flex items-center gap-3">
			<a
				href="/scis/{sciId}/biens/{bienId}"
				class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
			>
				<ArrowLeft class="h-4 w-4" />
				Retour au bien
			</a>
		</div>
		<h1 class="sci-page-title">Historique des baux</h1>
	</header>

	{#if loading}
		<div class="mt-6 space-y-4">
			{#each Array.from({ length: 3 }) as _}
				<div class="h-32 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
			{/each}
		</div>
	{:else if error}
		<div class="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30">
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={loadBaux}
				class="mt-3 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				Réessayer
			</button>
		</div>
	{:else if baux.length === 0}
		<div class="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700">
			<Users class="mb-3 h-8 w-8 text-slate-400 dark:text-slate-500" />
			<p class="text-sm text-slate-500 dark:text-slate-400">Aucun bail enregistré pour ce bien.</p>
		</div>
	{:else}
		<!-- Timeline -->
		<div class="mt-6 space-y-4">
			{#each baux as bail, index (bail.id)}
				{@const statut = getStatut(bail.statut)}
				{@const isActive = bail.statut === 'en_cours'}
				<div
					class="relative rounded-2xl border p-6 transition-colors {isActive
						? 'border-emerald-200 bg-emerald-50/50 dark:border-emerald-900 dark:bg-emerald-950/20'
						: 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950'}"
				>
					<!-- Timeline connector -->
					{#if index < baux.length - 1}
						<div class="absolute -bottom-4 left-8 h-4 w-0.5 bg-slate-200 dark:bg-slate-700"></div>
					{/if}

					<div class="flex flex-wrap items-start justify-between gap-3">
						<!-- Left: dates + statut -->
						<div class="space-y-2">
							<div class="flex items-center gap-3">
								<span
									class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {statut.class}"
								>
									{statut.label}
								</span>
								{#if isActive}
									<span class="text-xs font-medium text-emerald-600 dark:text-emerald-400">
										Bail actif
									</span>
								{/if}
							</div>
							<div class="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
								<span class="inline-flex items-center gap-1.5">
									<Calendar class="h-3.5 w-3.5" />
									{formatFrDate(bail.date_debut)}
								</span>
								<span class="text-slate-400 dark:text-slate-600">→</span>
								<span class="inline-flex items-center gap-1.5">
									<Calendar class="h-3.5 w-3.5" />
									{bail.date_fin ? formatFrDate(bail.date_fin) : 'Indéterminée'}
								</span>
							</div>
						</div>

						<!-- Right: montants -->
						<div class="flex gap-4 text-right">
							<div>
								<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
									Loyer HC
								</p>
								<p class="text-sm font-bold text-slate-900 dark:text-slate-100">
									{formatEur(bail.loyer_hc)}
								</p>
							</div>
							<div>
								<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
									Charges
								</p>
								<p class="text-sm font-bold text-slate-900 dark:text-slate-100">
									{formatEur(bail.charges_provisions)}
								</p>
							</div>
							<div>
								<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
									Dépôt
								</p>
								<p class="text-sm font-bold text-slate-900 dark:text-slate-100">
									{formatEur(bail.depot_garantie)}
								</p>
							</div>
						</div>
					</div>

					<!-- Locataires -->
					{#if bail.locataires && bail.locataires.length > 0}
						<div class="mt-3 border-t border-slate-200 pt-3 dark:border-slate-800">
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
								{bail.locataires.length > 1 ? 'Locataires (colocation)' : 'Locataire'}
							</p>
							<div class="mt-1.5 flex flex-wrap gap-2">
								{#each bail.locataires as loc (loc.id)}
									<span
										class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
									>
										<Users class="h-3.5 w-3.5 text-slate-400" />
										{loc.prenom ? `${loc.prenom} ${loc.nom}` : loc.nom}
									</span>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Indice de révision -->
					{#if bail.revision_indice}
						<div class="mt-2">
							<span class="text-xs text-slate-500 dark:text-slate-400">
								Indice de révision : {bail.revision_indice}
							</span>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</section>
