<script lang="ts">
	import type { FicheBien, ObligationsData, ObligationStatus } from '$lib/api';
	import { fetchObligations } from '$lib/api';
	import { FileText, Pencil, Loader2, ChevronDown, ShieldCheck, ShieldAlert, ShieldQuestion } from 'lucide-svelte';
	import { page } from '$app/state';

	interface Props {
		bien: FicheBien;
		sciNom: string;
		isGerant: boolean;
		onGenerateQuittance?: () => void;
		generatingQuittance?: boolean;
	}

	let { bien, sciNom, isGerant, onGenerateQuittance, generatingQuittance = false }: Props = $props();

	let sciId = $derived(page.params.sciId!);

	const dpeColors: Record<string, string> = {
		A: 'bg-green-600 text-white',
		B: 'bg-green-400 text-white',
		C: 'bg-yellow-400 text-slate-900',
		D: 'bg-yellow-500 text-slate-900',
		E: 'bg-orange-400 text-white',
		F: 'bg-orange-600 text-white',
		G: 'bg-red-600 text-white'
	};

	const statutLabels: Record<string, { label: string; class: string }> = {
		actif: { label: 'Bail actif', class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300' },
		en_cours: { label: 'Bail actif', class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300' },
		vacant: { label: 'Vacant', class: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300' },
		travaux: { label: 'Travaux', class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' }
	};

	let bailStatut = $derived(bien.bail_actif ? (bien.bail_actif.statut ?? 'actif') : 'vacant');
	let statutInfo = $derived(statutLabels[bailStatut] ?? statutLabels['vacant']);

	// ── Obligations ──────────────────────────────────────────
	let obligations = $state<ObligationsData | null>(null);
	let obligationsLoading = $state(true);
	let showObligationsPopover = $state(false);

	$effect(() => {
		loadObligations();
	});

	async function loadObligations() {
		obligationsLoading = true;
		try {
			obligations = await fetchObligations(sciId, String(bien.id));
		} catch {
			obligations = null;
		} finally {
			obligationsLoading = false;
		}
	}

	const statusIcon: Record<ObligationStatus, string> = {
		ok: 'text-emerald-500',
		warning: 'text-amber-500',
		danger: 'text-rose-500',
		unknown: 'text-slate-400'
	};

	const statusBadge: Record<ObligationStatus, string> = {
		ok: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
		warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
		danger: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300',
		unknown: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
	};

	function statusEmoji(status: ObligationStatus): string {
		if (status === 'ok') return '\u2705';
		if (status === 'warning') return '\u26A0\uFE0F';
		if (status === 'danger') return '\u274C';
		return '\u2753';
	}

	function togglePopover() {
		showObligationsPopover = !showObligationsPopover;
	}

	const obligationsList = $derived(
		obligations
			? [obligations.pno, obligations.dpe, obligations.bail, obligations.locataire, obligations.depot_garantie]
			: []
	);
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<header class="sci-page-header">
	<p class="sci-eyebrow">{sciNom} / Biens</p>
	<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="sci-page-title">{bien.adresse}</h1>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
				{bien.ville} {bien.code_postal}
			</p>
		</div>
		{#if isGerant}
			<div class="flex gap-2">
				<a
					href="#section-identite"
					class="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
				>
					<Pencil class="h-4 w-4" />
					Modifier
				</a>
				<button
					onclick={onGenerateQuittance}
					disabled={generatingQuittance}
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
				>
					{#if generatingQuittance}
						<Loader2 class="h-4 w-4 animate-spin" />
						Génération...
					{:else}
						<FileText class="h-4 w-4" />
						Générer quittance
					{/if}
				</button>
			</div>
		{/if}
	</div>

	<div class="mt-3 flex flex-wrap items-center gap-2.5">
		{#if bien.type_locatif}
			<span class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
				{bien.type_locatif}
			</span>
		{/if}

		{#if bien.dpe_classe}
			<span class="inline-flex items-center rounded-full px-3 py-1 text-sm font-bold {dpeColors[bien.dpe_classe.toUpperCase()] ?? 'bg-slate-200 text-slate-700'}">
				DPE {bien.dpe_classe.toUpperCase()}
			</span>
		{/if}

		<span class="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium {statutInfo.class}">
			{statutInfo.label}
		</span>

		<!-- Obligations indicator -->
		{#if !obligationsLoading && obligations}
			<div class="relative">
				<button
					type="button"
					onclick={togglePopover}
					class="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
					aria-expanded={showObligationsPopover}
					aria-label="Obligations du bien"
				>
					{#each [obligations.pno, obligations.dpe, obligations.bail] as ob}
						<span class="inline-flex rounded-full px-1.5 py-0.5 text-xs {statusBadge[ob.status]}">
							{statusEmoji(ob.status)} {ob.label}
						</span>
					{/each}
					<ChevronDown class="ml-0.5 h-3 w-3 text-slate-400 transition-transform {showObligationsPopover ? 'rotate-180' : ''}" />
				</button>

				{#if showObligationsPopover}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<div class="fixed inset-0 z-40" onclick={() => { showObligationsPopover = false; }}></div>
					<div class="absolute left-0 top-full z-50 mt-2 w-80 rounded-xl border border-slate-200 bg-white p-4 shadow-xl dark:border-slate-700 dark:bg-slate-900">
						<h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							<ShieldCheck class="h-4 w-4 text-indigo-500" />
							Obligations
						</h3>
						<div class="space-y-2">
							{#each obligationsList as ob}
								<div class="flex items-start gap-2 rounded-lg px-3 py-2 {statusBadge[ob.status].replace('text-', 'bg-').split(' ')[0]}/20">
									<span class="mt-0.5 text-sm">{statusEmoji(ob.status)}</span>
									<div class="min-w-0 flex-1">
										<p class="text-sm font-medium text-slate-900 dark:text-slate-100">{ob.label}</p>
										<p class="text-xs text-slate-600 dark:text-slate-400">{ob.detail}</p>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</header>
