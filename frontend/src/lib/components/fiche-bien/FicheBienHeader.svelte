<script lang="ts">
	import type { FicheBien, ObligationsData, ObligationStatus } from '$lib/api';
	import { fetchObligations, cederBien } from '$lib/api';
	import { FileText, Pencil, Loader2, ChevronDown, ShieldCheck, ShieldAlert, ShieldQuestion, Download, HandCoins } from 'lucide-svelte';
	import { page } from '$app/state';
	import { addToast } from '$lib/components/ui/toast';

	interface Props {
		bien: FicheBien;
		sciNom: string;
		isGerant: boolean;
		onGenerateQuittance?: () => void;
		generatingQuittance?: boolean;
	}

	let { bien, sciNom, isGerant, onGenerateQuittance, generatingQuittance = false }: Props = $props();

	function exportBienCsv() {
		const b = bien;
		const bail = b.bail_actif;
		const loc = bail?.locataires?.[0];
		const rows = [
			['Champ', 'Valeur'],
			['Adresse', b.adresse], ['Ville', b.ville], ['Code postal', b.code_postal],
			['Type de bien', b.type_bien || ''], ['Type de location', b.type_locatif || ''],
			['Surface (m²)', String(b.surface_m2 || '')], ['Pièces', String(b.nb_pieces || '')],
			['DPE', b.dpe_classe || ''], ['Prix acquisition', String(b.prix_acquisition || '')],
			['Loyer CC', String(b.loyer_cc || '')], ['Charges', String(b.charges || '')],
			['---', '--- Bail ---'],
			['Bail début', bail?.date_debut || ''], ['Bail fin', bail?.date_fin || 'Indéterminée'],
			['Loyer HC', String(bail?.loyer_hc || '')], ['Charges locatives', String(bail?.charges_locatives || '')],
			['Dépôt garantie', String(bail?.depot_garantie || '')], ['Statut', bail?.statut || 'Aucun'],
			['---', '--- Locataire ---'],
			['Locataire', loc?.nom || 'Aucun'], ['Email', loc?.email || ''], ['Téléphone', loc?.telephone || ''],
			['---', '--- Rentabilité ---'],
			['Rentabilité brute', b.rentabilite?.brute?.toFixed(1) + '%' || ''],
			['Rentabilité nette', b.rentabilite?.nette?.toFixed(1) + '%' || ''],
			['Cashflow mensuel', String(b.rentabilite?.cashflow_mensuel || 0)],
			['Cashflow annuel', String(b.rentabilite?.cashflow_annuel || 0)],
		];
		const csv = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
		const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
		const a = document.createElement('a');
		a.href = URL.createObjectURL(blob);
		a.download = `fiche-bien-${b.adresse.replace(/[^a-zA-Z0-9]/g, '-')}.csv`;
		a.click();
	}

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

	type ObligationItem = { status: string; label: string; detail: string };

	$effect(() => {
		loadObligations();
	});

	function toItem(raw: any, label: string): ObligationItem {
		if (!raw) return { status: 'unknown', label, detail: 'Non disponible' };
		return {
			status: raw.valid ? 'ok' : 'danger',
			label,
			detail: raw.detail || '',
		};
	}

	async function loadObligations() {
		obligationsLoading = true;
		try {
			const raw = await fetchObligations(sciId, String(bien.id));
			// Transform API response {valid, detail} → {status, label, detail}
			obligations = {
				pno: toItem(raw.pno, 'PNO'),
				dpe: toItem(raw.dpe, 'DPE'),
				bail: toItem(raw.bail, 'Bail'),
				locataire: toItem(raw.locataire, 'Locataire'),
				depot_garantie: toItem(raw.depot_garantie, 'Dépôt'),
			} as any;
		} catch {
			obligations = null;
		} finally {
			obligationsLoading = false;
		}
	}

	const statusBadge: Record<string, string> = {
		ok: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
		warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
		danger: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300',
		unknown: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
	};

	function statusEmoji(status: string): string {
		if (status === 'ok') return '✅';
		if (status === 'warning') return '⚠️';
		if (status === 'danger') return '❌';
		return '❓';
	}

	function togglePopover() {
		showObligationsPopover = !showObligationsPopover;
	}

	const obligationsList = $derived(
		obligations
			? [obligations.pno, obligations.dpe, obligations.bail, obligations.locataire, obligations.depot_garantie].filter(Boolean)
			: []
	);

	// ── Cession du bien ──────────────────────────────────
	let showCessionForm = $state(false);
	let cessionSaving = $state(false);
	let cessionPrix = $state(0);
	let cessionDate = $state('');
	let cessionAcquereur = $state('');

	const plusValueBrute = $derived(
		cessionPrix > 0 && bien.prix_acquisition
			? cessionPrix - bien.prix_acquisition
			: null
	);

	function openCessionForm() {
		showCessionForm = true;
		cessionPrix = 0;
		cessionDate = new Date().toISOString().split('T')[0];
		cessionAcquereur = '';
	}

	async function submitCession() {
		if (cessionPrix <= 0 || !cessionDate || !cessionAcquereur.trim()) return;
		cessionSaving = true;
		try {
			await cederBien(sciId, String(bien.id), {
				prix_cession: cessionPrix,
				date_cession: cessionDate,
				acquereur: cessionAcquereur
			});
			addToast({ title: 'Cession enregistrée', description: `Le bien a été cédé pour ${cessionPrix.toLocaleString('fr-FR')} EUR.`, variant: 'success' });
			showCessionForm = false;
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible d\'enregistrer la cession.', variant: 'error' });
		} finally {
			cessionSaving = false;
		}
	}
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
				<button
					onclick={exportBienCsv}
					class="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
				>
					<Download class="h-4 w-4" />
					Exporter
				</button>
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
				<button
					onclick={openCessionForm}
					class="inline-flex items-center gap-2 rounded-lg border border-amber-200 bg-white px-4 py-2 text-sm font-medium text-amber-700 transition-colors hover:bg-amber-50 dark:border-amber-800 dark:bg-slate-900 dark:text-amber-400 dark:hover:bg-amber-950/30"
				>
					<HandCoins class="h-4 w-4" />
					Céder le bien
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

	<!-- Cession form -->
	{#if showCessionForm}
		<div class="mt-4 rounded-xl border border-amber-200 bg-amber-50/50 p-5 dark:border-amber-800/50 dark:bg-amber-950/20">
			<h3 class="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
				<HandCoins class="h-4 w-4 text-amber-600" />
				Céder le bien
			</h3>
			<div class="grid gap-4 sm:grid-cols-3">
				<div>
					<label for="cession-prix" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Prix de cession</label>
					<input
						id="cession-prix"
						type="number"
						min="0"
						bind:value={cessionPrix}
						placeholder="0"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
				<div>
					<label for="cession-date" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Date de cession</label>
					<input
						id="cession-date"
						type="date"
						bind:value={cessionDate}
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
				<div>
					<label for="cession-acquereur" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Acquéreur</label>
					<input
						id="cession-acquereur"
						type="text"
						bind:value={cessionAcquereur}
						placeholder="Nom de l'acquéreur"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
			</div>
			{#if plusValueBrute != null}
				<div class="mt-3 rounded-lg px-4 py-2.5 {plusValueBrute >= 0 ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-rose-100 dark:bg-rose-900/30'}">
					<p class="text-sm font-medium {plusValueBrute >= 0 ? 'text-emerald-800 dark:text-emerald-300' : 'text-rose-800 dark:text-rose-300'}">
						Plus-value brute estimée : {plusValueBrute.toLocaleString('fr-FR')} EUR
					</p>
					<p class="text-xs {plusValueBrute >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}">
						Prix d'acquisition : {bien.prix_acquisition?.toLocaleString('fr-FR')} EUR | Prix de cession : {cessionPrix.toLocaleString('fr-FR')} EUR
					</p>
				</div>
			{/if}
			<div class="mt-4 flex items-center justify-end gap-2">
				<button onclick={() => { showCessionForm = false; }} class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800">
					Annuler
				</button>
				<button
					onclick={submitCession}
					disabled={cessionSaving || cessionPrix <= 0 || !cessionAcquereur.trim()}
					class="inline-flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
				>
					{#if cessionSaving}<Loader2 class="h-4 w-4 animate-spin" />{/if}
					Enregistrer la cession
				</button>
			</div>
		</div>
	{/if}
</header>
