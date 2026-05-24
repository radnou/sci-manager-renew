<script lang="ts">
	import { CalendarDays, Clock, CheckCircle2, Check } from 'lucide-svelte';
	import type { SCIDetail } from '$lib/api';
	import { fetchCalendrierFiscalStatut, demarquerEcheanceFiscale, marquerEcheanceFiscaleFaite } from '$lib/api';
	import { addToast } from '$lib/components/ui/toast';

	export let sciId: string;
	export let sci: SCIDetail;

	type FiscalEvent = {
		key: string;
		label: string;
		date: Date;
		regime: string | null;
		description: string;
		daysUntil?: number;
	};

	let fiscalDoneMap: Record<string, boolean> = {};
	const currentYear = new Date().getFullYear();

	$: loadFiscalStatut(currentYear);

	async function loadFiscalStatut(annee: number) {
		try {
			fiscalDoneMap = await fetchCalendrierFiscalStatut(sciId, annee);
		} catch {
			fiscalDoneMap = {};
		}
	}

	async function toggleFiscalDone(key: string) {
		const wasDone = fiscalDoneMap[key] ?? false;
		// Optimistic update
		fiscalDoneMap = { ...fiscalDoneMap, [key]: !wasDone };
		try {
			if (wasDone) {
				await demarquerEcheanceFiscale(sciId, currentYear, key);
			} else {
				await marquerEcheanceFiscaleFaite(sciId, currentYear, key);
			}
		} catch {
			// Rollback
			fiscalDoneMap = { ...fiscalDoneMap, [key]: wasDone };
			addToast({ title: 'Erreur', description: 'Impossible de mettre à jour le statut.', variant: 'error' });
		}
	}

	$: regime = (sci.regime_fiscal ?? '').toUpperCase();

	// Dynamic fiscal calendar based on exercise closing date
	$: clotureRaw = (sci as any).date_cloture_exercice as string | undefined;
	$: clotureDate = clotureRaw ? new Date(clotureRaw) : null;
	$: clotureMonth = clotureDate ? clotureDate.getMonth() : 11; // default: December
	$: clotureDay = clotureDate ? clotureDate.getDate() : 31;
	$: clotureLabel = clotureDate
		? clotureDate.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })
		: null;

	function addMonths(date: Date, months: number): Date {
		const d = new Date(date);
		d.setMonth(d.getMonth() + months);
		return d;
	}

	$: clotureRef = new Date(currentYear, clotureMonth, clotureDay);
	$: agDate = addMonths(clotureRef, 6);
	$: liasseIsDate = addMonths(clotureRef, 3);

	// V14 — CFE conditional on type_locatif
	$: biensList = (sci.biens ?? []) as Array<{ type_locatif?: string | null }>;
	$: hasCfeBiens = biensList.some(b => b.type_locatif === 'meuble' || b.type_locatif === 'commercial' || b.type_locatif === 'mixte');
	$: biensCount = sci.biens_count ?? sci.biens?.length ?? 0;

	$: allDeadlines = [
		...(regime === 'IR' ? [
			{ key: 'declaration_2072', label: 'Déclaration 2072', date: new Date(currentYear, 4, 20), regime: 'IR', description: 'Déclaration des résultats de la SCI à l\'IR' },
			{ key: 'declaration_2044', label: 'Déclaration 2044', date: new Date(currentYear, 4, 31), regime: 'IR', description: 'Déclaration individuelle des revenus fonciers (chaque associé)' },
		] : []),
		...(regime === 'IS' ? [
			{ key: 'liasse_fiscale_is', label: 'Liasse fiscale IS', date: liasseIsDate, regime: 'IS', description: `Liasse fiscale pour SCI à l'IS (3 mois post-clôture)${clotureLabel ? ` — basé sur la clôture au ${clotureLabel}` : ''}` },
		] : []),
		{ key: 'ag_annuelle', label: 'AG annuelle', date: agDate, regime: null, description: `Assemblée générale obligatoire (6 mois post-clôture)${clotureLabel ? ` — basé sur la clôture au ${clotureLabel}` : ''}` },
		{ key: 'taxe_fonciere', label: 'Taxe foncière', date: new Date(currentYear, 9, 15), regime: null, description: 'Paiement de la taxe foncière' },
		...(hasCfeBiens ? [
			{ key: 'cfe', label: 'CFE', date: new Date(currentYear, 11, 15), regime: null, description: 'Cotisation Foncière des Entreprises' },
		] : biensCount > 0 ? [
			{ key: 'cfe', label: 'CFE', date: new Date(currentYear, 11, 15), regime: null, description: 'Exonéré (biens nus résidentiels)' },
		] : []),
	] as FiscalEvent[];

	const now = new Date();
	$: fiscalEvents = allDeadlines
			.map(e => ({ ...e, daysUntil: Math.ceil((e.date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)) }))
			.sort((a, b) => a.date.getTime() - b.date.getTime());

	function deadlineStatus(daysUntil: number): { color: string; iconColor: string; bg: string; label: string } {
		if (daysUntil < 0) return { color: 'text-slate-400 dark:text-slate-500', iconColor: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-950/30', label: 'Passé' };
		if (daysUntil <= 15) return { color: 'text-rose-700 dark:text-rose-300', iconColor: 'text-rose-500', bg: 'bg-rose-50 dark:bg-rose-950/30', label: `${daysUntil}j` };
		if (daysUntil <= 45) return { color: 'text-amber-700 dark:text-amber-300', iconColor: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-950/30', label: `${daysUntil}j` };
		return { color: 'text-slate-600 dark:text-slate-400', iconColor: 'text-slate-400', bg: 'bg-slate-50 dark:bg-slate-900', label: `${daysUntil}j` };
	}
</script>

<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="flex items-center gap-2">
		<CalendarDays class="h-5 w-5 text-sky-600 dark:text-sky-400" />
		<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Calendrier fiscal {currentYear}</h2>
		{#if regime}
			<span class="rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">{regime}</span>
		{/if}
	</div>
	<div class="mt-4 space-y-2">
		{#each fiscalEvents as event}
			{@const status = deadlineStatus(event.daysUntil ?? 0)}
			{@const isDone = fiscalDoneMap[event.key] ?? false}
			<div class="flex items-center gap-3 rounded-xl {isDone ? 'bg-emerald-50 dark:bg-emerald-950/30' : status.bg} px-4 py-3">
				<button
					type="button"
					on:click={() => toggleFiscalDone(event.key)}
					class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-white/80 transition-colors hover:bg-white dark:bg-slate-800/80 dark:hover:bg-slate-700/80"
					title={isDone ? 'Marquer comme non fait' : 'Marquer comme fait'}
					aria-label={isDone ? `${event.label} : fait` : `${event.label} : en attente`}
				>
					{#if isDone}
						<Check class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
					{:else if (event.daysUntil ?? 0) < 0}
						<CheckCircle2 class="h-4 w-4 {status.iconColor}" />
					{:else}
						<Clock class="h-4 w-4 {status.iconColor}" />
					{/if}
				</button>
				<div class="min-w-0 flex-1">
					<div class="flex items-center justify-between gap-2">
						<p class="text-sm font-medium {isDone ? 'text-emerald-700 line-through dark:text-emerald-400' : (event.daysUntil ?? 0) < 0 ? 'text-slate-400 dark:text-slate-500' : 'text-slate-900 dark:text-slate-100'}">
							{event.label}
							{#if isDone}
								<span class="ml-1.5 text-xs font-normal text-emerald-600 dark:text-emerald-400">fait</span>
							{/if}
						</p>
						<span class="flex-shrink-0 text-xs font-semibold {isDone ? 'text-emerald-600 dark:text-emerald-400' : status.color}">
							{isDone ? 'Fait' : status.label}
						</span>
					</div>
					<p class="text-xs {isDone ? 'text-emerald-600/70 dark:text-emerald-400/70' : (event.daysUntil ?? 0) < 0 ? 'text-slate-400 dark:text-slate-500' : 'text-slate-500 dark:text-slate-400'}">
						{event.date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} — {event.description}
					</p>
				</div>
			</div>
		{/each}
	</div>
	{#if !regime}
		<p class="mt-3 text-xs text-amber-600 dark:text-amber-400">
			Renseignez le régime fiscal (IR/IS) de cette SCI pour afficher les échéances spécifiques.
		</p>
	{/if}
</div>
