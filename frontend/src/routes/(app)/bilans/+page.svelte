<script lang="ts">
	import { page } from '$app/state';
	import type { BilanData, BilanSci, BilanBien, SCIOverview } from '$lib/api';
	import { fetchBilan, fetchBilanPeriodes, downloadBilanPdf, fetchScis } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import {
		FileSpreadsheet,
		TrendingUp,
		TrendingDown,
		Wallet,
		Building2,
		Percent,
		RefreshCw,
		Download,
		ChevronRight
	} from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { addToast } from '$lib/components/ui/toast';

	let data: BilanData | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);
	let refreshing = $state(false);
	let downloading = $state(false);

	// Read URL query params for deep-linking: /bilans?scope=sci&scope_id=xxx&periode=2026-03
	const urlScope = page.url.searchParams.get('scope');
	const urlScopeId = page.url.searchParams.get('scope_id');
	const urlPeriode = page.url.searchParams.get('periode');

	// Filters
	let periodes: string[] = $state([]);
	let selectedPeriode = $state(urlPeriode ?? '');
	let scope: 'portefeuille' | 'sci' | 'bien' = $state(
		(urlScope === 'sci' || urlScope === 'bien') ? urlScope : 'portefeuille'
	);
	let scopeId: string | undefined = $state(urlScopeId ?? undefined);
	let scis: SCIOverview[] = $state([]);

	// Collapsible state
	let expandedScis: Record<string, boolean> = $state({});
	let expandedBiens: Record<string, boolean> = $state({});

	// Init: load periodes + SCIs
	$effect(() => {
		Promise.all([fetchBilanPeriodes(), fetchScis()])
			.then(([p, s]) => {
				periodes = p;
				scis = s;
				if (p.length > 0 && !selectedPeriode) {
					selectedPeriode = p[0];
				}
			})
			.catch((err: Error) => {
				error = err?.message ?? 'Impossible de charger les periodes.';
				loading = false;
			});
	});

	// Load bilan when filters change
	$effect(() => {
		if (selectedPeriode) {
			loadBilan(false);
		}
	});

	async function loadBilan(forceRefresh: boolean) {
		if (!selectedPeriode) return;
		if (forceRefresh) {
			refreshing = true;
		} else {
			loading = true;
		}
		error = null;
		try {
			data = await fetchBilan(selectedPeriode, scope, scopeId, forceRefresh);
			// Auto-expand all SCIs
			if (data) {
				for (const sci of data.scis) {
					expandedScis[String(sci.sci_id)] = true;
					for (const bien of sci.biens) {
						expandedBiens[`${sci.sci_id}-${bien.bien_id}`] = true;
					}
				}
			}
		} catch (err: unknown) {
			const msg = err instanceof Error ? err.message : 'Impossible de charger le bilan.';
			error = msg;
			data = null;
		} finally {
			loading = false;
			refreshing = false;
		}
	}

	async function handleDownloadPdf() {
		downloading = true;
		try {
			const blob = await downloadBilanPdf(selectedPeriode, scope, scopeId);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `bilan_${selectedPeriode}_${scope}.pdf`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			addToast({
				title: 'PDF telecharge',
				description: `Bilan ${formatPeriodeLabel(selectedPeriode)} exporte.`,
				variant: 'success'
			});
		} catch (err: unknown) {
			const msg = err instanceof Error ? err.message : 'Impossible de telecharger le PDF.';
			addToast({ title: 'Erreur export', description: msg, variant: 'error' });
		} finally {
			downloading = false;
		}
	}

	function cashflowColor(value: number): string {
		if (value > 0) return 'text-emerald-600 dark:text-emerald-400';
		if (value < 0) return 'text-rose-600 dark:text-rose-400';
		return 'text-slate-700 dark:text-slate-300';
	}

	function statusColor(statut?: string | null): string {
		if (statut === 'paye') return 'text-emerald-600 dark:text-emerald-400';
		if (statut === 'en_retard' || statut === 'retard') return 'text-rose-600 dark:text-rose-400';
		return 'text-slate-700 dark:text-slate-300';
	}

	function formatPeriodeLabel(p: string): string {
		if (!p) return '';
		const [year, month] = p.split('-');
		const months = [
			'Janvier',
			'Fevrier',
			'Mars',
			'Avril',
			'Mai',
			'Juin',
			'Juillet',
			'Aout',
			'Septembre',
			'Octobre',
			'Novembre',
			'Decembre'
		];
		const idx = parseInt(month, 10) - 1;
		return `${months[idx] ?? month} ${year}`;
	}

	function formatDate(d: string): string {
		if (!d) return '';
		const parts = d.split('-');
		if (parts.length >= 3) return `${parts[2]}/${parts[1]}`;
		return d;
	}

	function toggleSci(sciId: string) {
		expandedScis[sciId] = !expandedScis[sciId];
	}

	function toggleBien(key: string) {
		expandedBiens[key] = !expandedBiens[key];
	}

	function handleScopeChange(newScope: 'portefeuille' | 'sci' | 'bien') {
		scope = newScope;
		if (newScope === 'portefeuille') {
			scopeId = undefined;
		}
	}
</script>

<svelte:head><title>Bilans Mensuels | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Comptabilite</p>
		<h1 class="sci-page-title">Bilans Mensuels</h1>
	</header>

	<!-- Filters row -->
	<div class="mt-4 flex flex-wrap items-center gap-3">
		<!-- Periode selector -->
		<div class="flex items-center gap-2">
			<label for="periode-select" class="text-sm font-medium text-slate-600 dark:text-slate-400"
				>Mois</label
			>
			<select
				id="periode-select"
				bind:value={selectedPeriode}
				class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-900 transition-colors focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
			>
				{#each periodes as p}
					<option value={p}>{formatPeriodeLabel(p)}</option>
				{/each}
			</select>
		</div>

		<!-- Scope selector -->
		<div class="flex items-center gap-1">
			{#each [
				{ value: 'portefeuille', label: 'Portefeuille' },
				{ value: 'sci', label: 'Par SCI' },
				{ value: 'bien', label: 'Par Bien' }
			] as opt}
				<button
					onclick={() => handleScopeChange(opt.value as 'portefeuille' | 'sci' | 'bien')}
					class="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {scope === opt.value
						? 'bg-sky-600 text-white'
						: 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700'}"
				>
					{opt.label}
				</button>
			{/each}
		</div>

		<!-- SCI selector (when scope = sci) -->
		{#if scope === 'sci' && scis.length > 0}
			<select
				bind:value={scopeId}
				class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-900 transition-colors focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
			>
				<option value={undefined}>Toutes les SCI</option>
				{#each scis as sci}
					<option value={String(sci.id)}>{sci.nom}</option>
				{/each}
			</select>
		{/if}

		<!-- Spacer -->
		<div class="flex-1"></div>

		<!-- Actions -->
		<div class="flex items-center gap-2">
			<Button
				onclick={() => loadBilan(true)}
				disabled={refreshing}
				variant="outline"
				class="shrink-0"
			>
				<RefreshCw class="mr-2 h-4 w-4 {refreshing ? 'animate-spin' : ''}" />
				{refreshing ? 'Actualisation...' : 'Rafraichir'}
			</Button>
			<Button onclick={handleDownloadPdf} disabled={downloading || !data} variant="outline" class="shrink-0">
				<Download class="mr-2 h-4 w-4" />
				{downloading ? 'Export...' : 'PDF'}
			</Button>
		</div>
	</div>

	{#if loading}
		<div class="sci-loading" aria-label="Chargement"></div>
	{:else if error}
		<div
			class="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30"
		>
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={() => loadBilan(false)}
				class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				<RefreshCw class="h-4 w-4" />
				Reessayer
			</button>
		</div>
	{:else if data && data.scis.length === 0}
		<div class="mt-6">
			<EmptyState
				icon={FileSpreadsheet}
				title="Aucune donnee pour cette periode"
				description="Enregistrez des loyers et des charges sur vos biens pour voir apparaitre votre bilan mensuel."
				ctaText="Aller au dashboard"
				ctaHref="/dashboard"
			/>
		</div>
	{:else if data}
		<!-- Grand Livre table -->
		<div
			class="mt-6 rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950"
		>
			<div class="overflow-x-auto">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-slate-200 dark:border-slate-700">
							<th
								class="px-4 pb-3 pt-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Date</th
							>
							<th
								class="px-4 pb-3 pt-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Libelle</th
							>
							<th
								class="px-4 pb-3 pt-4 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Entrees</th
							>
							<th
								class="px-4 pb-3 pt-4 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Sorties</th
							>
							<th
								class="px-4 pb-3 pt-4 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
								>Solde</th
							>
						</tr>
					</thead>
					<tbody>
						{#each data.scis as sci (sci.sci_id)}
							<!-- SCI header row -->
							<tr
								class="cursor-pointer border-b border-slate-100 bg-slate-50/70 transition-colors hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:bg-slate-800/50"
								onclick={() => toggleSci(String(sci.sci_id))}
							>
								<td class="px-4 py-3" colspan="2">
									<div class="flex items-center gap-2">
										<ChevronRight
											class="h-4 w-4 text-slate-400 transition-transform {expandedScis[
												String(sci.sci_id)
											]
												? 'rotate-90'
												: ''}"
										/>
										<Building2 class="h-4 w-4 text-sky-500" />
										<span
											class="font-semibold text-slate-900 dark:text-slate-100"
											>{sci.sci_nom}</span
										>
									</div>
								</td>
								<td
									class="px-4 py-3 text-right font-semibold text-emerald-700 dark:text-emerald-400"
									>{formatEur(sci.total_entrees)}</td
								>
								<td
									class="px-4 py-3 text-right font-semibold text-rose-700 dark:text-rose-400"
									>{formatEur(sci.total_sorties)}</td
								>
								<td class="px-4 py-3 text-right font-semibold {cashflowColor(sci.solde)}"
									>{formatEur(sci.solde)}</td
								>
							</tr>

							{#if expandedScis[String(sci.sci_id)]}
								{#each sci.biens as bien (bien.bien_id)}
									<!-- Bien header row -->
									<tr
										class="cursor-pointer border-b border-slate-100 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900/30"
										onclick={() =>
											toggleBien(`${sci.sci_id}-${bien.bien_id}`)}
									>
										<td class="px-4 py-2.5" colspan="2">
											<div class="flex items-center gap-2 pl-6">
												<ChevronRight
													class="h-3.5 w-3.5 text-slate-400 transition-transform {expandedBiens[
														`${sci.sci_id}-${bien.bien_id}`
													]
														? 'rotate-90'
														: ''}"
												/>
												<span
													class="font-medium text-slate-700 dark:text-slate-300"
													>{bien.adresse}{bien.ville
														? `, ${bien.ville}`
														: ''}</span
												>
											</div>
										</td>
										<td
											class="px-4 py-2.5 text-right text-sm text-emerald-600 dark:text-emerald-400"
											>{formatEur(bien.total_entrees)}</td
										>
										<td
											class="px-4 py-2.5 text-right text-sm text-rose-600 dark:text-rose-400"
											>{formatEur(bien.total_sorties)}</td
										>
										<td
											class="px-4 py-2.5 text-right text-sm font-medium {cashflowColor(
												bien.solde
											)}">{formatEur(bien.solde)}</td
										>
									</tr>

									{#if expandedBiens[`${sci.sci_id}-${bien.bien_id}`]}
										{#each bien.lignes as ligne}
											{#if ligne.type !== 'sous_total_bien'}
												<tr
													class="border-b border-slate-50 dark:border-slate-800/50"
												>
													<td
														class="px-4 py-2 text-xs text-slate-500 dark:text-slate-400"
													>
														{formatDate(ligne.date)}
													</td>
													<td class="px-4 py-2">
														<span
															class="pl-12 text-sm {ligne.type === 'loyer'
																? statusColor(ligne.statut)
																: 'text-slate-600 dark:text-slate-400'}"
														>
															{ligne.libelle}
														</span>
													</td>
													<td
														class="px-4 py-2 text-right text-sm {ligne.entrees > 0
															? 'text-emerald-600 dark:text-emerald-400'
															: 'text-slate-300 dark:text-slate-700'}"
													>
														{ligne.entrees > 0
															? formatEur(ligne.entrees)
															: ''}
													</td>
													<td
														class="px-4 py-2 text-right text-sm {ligne.sorties > 0
															? 'text-rose-600 dark:text-rose-400'
															: 'text-slate-300 dark:text-slate-700'}"
													>
														{ligne.sorties > 0
															? formatEur(ligne.sorties)
															: ''}
													</td>
													<td
														class="px-4 py-2 text-right text-sm {cashflowColor(
															ligne.solde
														)}"
													>
														{formatEur(ligne.solde)}
													</td>
												</tr>
											{/if}
										{/each}

										<!-- Bien subtotal -->
										<tr
											class="border-b border-slate-200 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-900/30"
										>
											<td class="px-4 py-2"></td>
											<td class="px-4 py-2">
												<span
													class="pl-6 text-xs font-semibold text-slate-500 uppercase dark:text-slate-400"
													>Sous-total bien</span
												>
											</td>
											<td
												class="px-4 py-2 text-right text-xs font-semibold text-emerald-700 dark:text-emerald-400"
												>{formatEur(bien.total_entrees)}</td
											>
											<td
												class="px-4 py-2 text-right text-xs font-semibold text-rose-700 dark:text-rose-400"
												>{formatEur(bien.total_sorties)}</td
											>
											<td
												class="px-4 py-2 text-right text-xs font-semibold {cashflowColor(
													bien.solde
												)}">{formatEur(bien.solde)}</td
											>
										</tr>
									{/if}
								{/each}

								<!-- SCI subtotal -->
								<tr
									class="border-b border-slate-200 bg-slate-100/80 dark:border-slate-700 dark:bg-slate-800/50"
								>
									<td class="px-4 py-2.5"></td>
									<td class="px-4 py-2.5">
										<span
											class="text-xs font-bold text-slate-600 uppercase dark:text-slate-300"
											>Sous-total {sci.sci_nom}</span
										>
									</td>
									<td
										class="px-4 py-2.5 text-right text-sm font-bold text-emerald-700 dark:text-emerald-400"
										>{formatEur(sci.total_entrees)}</td
									>
									<td
										class="px-4 py-2.5 text-right text-sm font-bold text-rose-700 dark:text-rose-400"
										>{formatEur(sci.total_sorties)}</td
									>
									<td
										class="px-4 py-2.5 text-right text-sm font-bold {cashflowColor(
											sci.solde
										)}">{formatEur(sci.solde)}</td
									>
								</tr>
							{/if}
						{/each}

						<!-- Portfolio total -->
						<tr class="bg-slate-900 dark:bg-slate-50/5">
							<td class="px-4 py-3.5"></td>
							<td class="px-4 py-3.5">
								<span class="text-sm font-bold text-white uppercase dark:text-slate-100"
									>Total Portefeuille</span
								>
							</td>
							<td
								class="px-4 py-3.5 text-right text-sm font-bold text-emerald-400"
								>{formatEur(data.total_entrees)}</td
							>
							<td class="px-4 py-3.5 text-right text-sm font-bold text-rose-400"
								>{formatEur(data.total_sorties)}</td
							>
							<td
								class="px-4 py-3.5 text-right text-sm font-bold {data.solde >= 0
									? 'text-emerald-400'
									: 'text-rose-400'}">{formatEur(data.solde)}</td
							>
						</tr>
					</tbody>
				</table>
			</div>
		</div>

		<!-- KPI cards -->
		<div class="sci-stagger mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
			<!-- Revenus attendus vs encaisses -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<TrendingUp class="h-5 w-5 text-emerald-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Revenus encaisses
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
					{formatEur(data.kpis.revenus_encaisses)}
				</p>
				<p class="mt-1 text-xs text-slate-400">
					sur {formatEur(data.kpis.revenus_attendus)} attendus
				</p>
			</div>

			<!-- Charges totales -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<TrendingDown class="h-5 w-5 text-rose-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Charges totales
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold text-rose-600 dark:text-rose-400">
					{formatEur(data.kpis.charges_totales)}
				</p>
			</div>

			<!-- Cashflow net -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<Wallet class="h-5 w-5 text-sky-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Cashflow net
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold {cashflowColor(data.kpis.cashflow_net)}">
					{formatEur(data.kpis.cashflow_net)}
				</p>
			</div>

			<!-- Taux de recouvrement -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<Percent class="h-5 w-5 text-amber-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Recouvrement
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
					{data.kpis.taux_recouvrement.toFixed(1)}%
				</p>
			</div>

			<!-- Nombre de biens / SCIs -->
			<div
				class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
			>
				<div class="flex items-center gap-2">
					<Building2 class="h-5 w-5 text-indigo-500" />
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Patrimoine
					</p>
				</div>
				<p class="mt-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
					{data.kpis.nb_biens} bien{data.kpis.nb_biens > 1 ? 's' : ''}
				</p>
				<p class="mt-1 text-xs text-slate-400">
					{data.kpis.nb_scis} SCI{data.kpis.nb_scis > 1 ? 's' : ''}
				</p>
			</div>
		</div>
	{/if}
</section>
