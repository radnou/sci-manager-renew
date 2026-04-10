<script lang="ts">
	import { fetchEcheances, fetchScis, type Echeance, type EcheancesResume, type SCIOverview } from '$lib/api';
	import { formatFrDate } from '$lib/high-value/formatters';
	import {
		CalendarClock,
		AlertTriangle,
		Clock,
		CheckCircle,
		ArrowRight,
		Filter,
		XCircle
	} from 'lucide-svelte';

	let echeances: Echeance[] = $state([]);
	let resume: EcheancesResume = $state({ depassee: 0, critique: 0, urgente: 0, normale: 0, lointaine: 0 });
	let scis: SCIOverview[] = $state([]);
	let loading = $state(true);
	let error = $state('');

	// Filters
	let filterSci = $state('');
	let filterType = $state('');
	let filterUrgence = $state('');

	const typeOptions = [
		{ value: '', label: 'Tous les types' },
		{ value: 'AG', label: 'Assemblées générales' },
		{ value: 'Déclarations', label: 'Déclarations' },
		{ value: 'PNO', label: 'Assurance PNO' },
		{ value: 'Diagnostics', label: 'Diagnostics' },
		{ value: 'Bail', label: 'Bail' },
		{ value: 'Loyers', label: 'Loyers' }
	];

	const urgenceOptions = [
		{ value: '', label: 'Toutes les urgences' },
		{ value: 'depassee', label: 'Dépassées' },
		{ value: 'critique', label: 'Critiques' },
		{ value: 'urgente', label: 'Urgentes' },
		{ value: 'normale', label: 'Normales' },
		{ value: 'lointaine', label: 'Lointaines' }
	];

	const urgenceConfig: Record<string, { label: string; badgeClass: string; cardBorder: string; icon: typeof AlertTriangle }> = {
		depassee: {
			label: 'Dépassées',
			badgeClass: 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900',
			cardBorder: 'border-l-slate-900 dark:border-l-slate-100',
			icon: XCircle
		},
		critique: {
			label: 'Critiques',
			badgeClass: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
			cardBorder: 'border-l-red-500',
			icon: AlertTriangle
		},
		urgente: {
			label: 'Urgentes',
			badgeClass: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
			cardBorder: 'border-l-orange-500',
			icon: Clock
		},
		normale: {
			label: 'Normales',
			badgeClass: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
			cardBorder: 'border-l-emerald-500',
			icon: CheckCircle
		},
		lointaine: {
			label: 'Lointaines',
			badgeClass: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
			cardBorder: 'border-l-slate-300 dark:border-l-slate-600',
			icon: CalendarClock
		}
	};

	const kpiCards = $derived([
		{ key: 'depassee' as const, label: 'Depassees', count: resume.depassee, bgClass: 'bg-slate-900 dark:bg-slate-100', textClass: 'text-white dark:text-slate-900', countClass: 'text-white dark:text-slate-900' },
		{ key: 'critique' as const, label: 'Critiques', count: resume.critique, bgClass: 'bg-red-50 dark:bg-red-900/20', textClass: 'text-red-800 dark:text-red-300', countClass: 'text-red-600 dark:text-red-400' },
		{ key: 'urgente' as const, label: 'Urgentes', count: resume.urgente, bgClass: 'bg-orange-50 dark:bg-orange-900/20', textClass: 'text-orange-800 dark:text-orange-300', countClass: 'text-orange-600 dark:text-orange-400' },
		{ key: 'normale' as const, label: 'Normales', count: resume.normale, bgClass: 'bg-emerald-50 dark:bg-emerald-900/20', textClass: 'text-emerald-800 dark:text-emerald-300', countClass: 'text-emerald-600 dark:text-emerald-400' },
		{ key: 'lointaine' as const, label: 'Lointaines', count: resume.lointaine, bgClass: 'bg-slate-50 dark:bg-slate-800', textClass: 'text-slate-600 dark:text-slate-400', countClass: 'text-slate-700 dark:text-slate-300' }
	]);

	async function loadData() {
		loading = true;
		error = '';
		try {
			const [echeancesData, scisData] = await Promise.all([
				fetchEcheances(filterSci || undefined),
				fetchScis()
			]);
			echeances = echeancesData.echeances;
			resume = echeancesData.resume;
			scis = scisData;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Erreur lors du chargement';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		loadData();
	});

	// Re-fetch when SCI filter changes
	async function onSciFilterChange() {
		loading = true;
		error = '';
		try {
			const data = await fetchEcheances(filterSci || undefined);
			echeances = data.echeances;
			resume = data.resume;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Erreur lors du chargement';
		} finally {
			loading = false;
		}
	}

	const filteredEcheances = $derived(() => {
		let result = echeances;
		if (filterType) {
			result = result.filter((e) => e.type === filterType);
		}
		if (filterUrgence) {
			result = result.filter((e) => e.urgence === filterUrgence);
		}
		return result;
	});

	const groupedEcheances = $derived(() => {
		const filtered = filteredEcheances();
		const order: Array<Echeance['urgence']> = ['depassee', 'critique', 'urgente', 'normale', 'lointaine'];
		const groups: Array<{ urgence: Echeance['urgence']; items: Echeance[] }> = [];
		for (const urg of order) {
			const items = filtered.filter((e) => e.urgence === urg);
			if (items.length > 0) {
				groups.push({ urgence: urg, items });
			}
		}
		return groups;
	});

	function relativeDays(dateStr: string): string {
		const now = new Date();
		const target = new Date(dateStr);
		const diffMs = target.getTime() - now.getTime();
		const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
		if (diffDays === 0) return "aujourd'hui";
		if (diffDays === 1) return 'demain';
		if (diffDays === -1) return 'hier';
		if (diffDays > 0) return `dans ${diffDays} jour${diffDays > 1 ? 's' : ''}`;
		return `il y a ${Math.abs(diffDays)} jour${Math.abs(diffDays) > 1 ? 's' : ''}`;
	}
</script>

<svelte:head>
	<title>Échéances | GérerSCI</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8 sm:px-6">
	<!-- Header -->
	<div class="mb-8">
		<p class="text-sm font-medium text-slate-500 dark:text-slate-400">Pilotage</p>
		<h1 class="mt-1 text-2xl font-bold text-slate-900 dark:text-white">Échéances</h1>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-20">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-sky-600"></div>
		</div>
	{:else if error}
		<div class="rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/20">
			<AlertTriangle class="mx-auto mb-2 h-8 w-8 text-red-400" />
			<p class="text-sm text-red-600 dark:text-red-400">{error}</p>
			<button
				onclick={loadData}
				class="mt-3 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
			>
				Réessayer
			</button>
		</div>
	{:else}
		<!-- KPI Cards -->
		<div class="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
			{#each kpiCards as kpi (kpi.key)}
				<button
					type="button"
					onclick={() => { filterUrgence = filterUrgence === kpi.key ? '' : kpi.key; }}
					class="rounded-xl p-4 text-center transition-all hover:ring-2 hover:ring-sky-300 {kpi.bgClass} {filterUrgence === kpi.key ? 'ring-2 ring-sky-500' : ''}"
				>
					<p class="text-2xl font-bold {kpi.countClass}">{kpi.count}</p>
					<p class="mt-1 text-xs font-medium {kpi.textClass}">{kpi.label}</p>
				</button>
			{/each}
		</div>

		<!-- Filters -->
		<div class="mb-6 flex flex-wrap items-center gap-3">
			<Filter class="h-4 w-4 text-slate-400" />
			<select
				bind:value={filterSci}
				onchange={onSciFilterChange}
				class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
			>
				<option value="">Toutes les SCI</option>
				{#each scis as sci (sci.id)}
					<option value={String(sci.id)}>{sci.nom}</option>
				{/each}
			</select>
			<select
				bind:value={filterType}
				class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
			>
				{#each typeOptions as opt (opt.value)}
					<option value={opt.value}>{opt.label}</option>
				{/each}
			</select>
			<select
				bind:value={filterUrgence}
				class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
			>
				{#each urgenceOptions as opt (opt.value)}
					<option value={opt.value}>{opt.label}</option>
				{/each}
			</select>
			{#if filterSci || filterType || filterUrgence}
				<button
					onclick={() => { filterSci = ''; filterType = ''; filterUrgence = ''; onSciFilterChange(); }}
					class="text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
				>
					Reinitialiser
				</button>
			{/if}
		</div>

		<!-- Grouped echeances list -->
		{#if groupedEcheances().length === 0}
			<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-16 dark:border-slate-700">
				<CalendarClock class="mb-3 h-10 w-10 text-slate-400 dark:text-slate-500" />
				<p class="text-sm font-medium text-slate-500 dark:text-slate-400">Aucune echeance trouvee.</p>
			</div>
		{:else}
			<div class="space-y-8">
				{#each groupedEcheances() as group (group.urgence)}
					{@const config = urgenceConfig[group.urgence]}
					<div>
						<div class="mb-3 flex items-center gap-2">
							<config.icon class="h-4 w-4" />
							<h2 class="text-sm font-semibold text-slate-700 dark:text-slate-300">
								{config.label}
								<span class="ml-1 text-slate-400">({group.items.length})</span>
							</h2>
						</div>
						<div class="space-y-3">
							{#each group.items as ech (ech.titre + ech.date_echeance + ech.entite)}
								<div
									class="rounded-xl border border-slate-200 border-l-4 bg-white p-4 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800/70 {config.cardBorder}"
								>
									<div class="flex flex-wrap items-start justify-between gap-3">
										<div class="min-w-0 flex-1">
											<div class="flex flex-wrap items-center gap-2">
												<span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium {config.badgeClass}">
													{config.label}
												</span>
												<span class="text-xs text-slate-400 dark:text-slate-500">{ech.type}</span>
											</div>
											<h3 class="mt-1.5 text-sm font-semibold text-slate-900 dark:text-slate-100">
												{ech.titre}
											</h3>
											<p class="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
												{ech.description}
											</p>
											<div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
												<span class="inline-flex items-center gap-1">
													<CalendarClock class="h-3 w-3" />
													{formatFrDate(ech.date_echeance)}
													<span class="font-medium {group.urgence === 'depassee' ? 'text-slate-900 dark:text-white' : group.urgence === 'critique' ? 'text-red-600 dark:text-red-400' : ''}">
														({relativeDays(ech.date_echeance)})
													</span>
												</span>
												<span>{ech.entite}</span>
											</div>
											{#if ech.reference_legale}
												<p class="mt-1.5 text-xs text-slate-400 dark:text-slate-500 italic">
													{ech.reference_legale}
												</p>
											{/if}
											{#if ech.consequence}
												<p class="mt-1 text-xs font-medium {group.urgence === 'depassee' || group.urgence === 'critique' ? 'text-red-600 dark:text-red-400' : 'text-slate-500 dark:text-slate-400'}">
													{ech.consequence}
												</p>
											{/if}
										</div>
										{#if ech.action_url}
											<a
												href={ech.action_url}
												class="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
											>
												Voir
												<ArrowRight class="h-3.5 w-3.5" />
											</a>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>
