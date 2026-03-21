<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail, Fiscalite, ResumeFiscalData, AssocieQuotePart } from '$lib/api';
	import { fetchFiscalite, generateCerfa2044Pdf, downloadResumeFiscalPdf, downloadReport2042Pdf, fetchResumeFiscal, createFiscalite, deleteFiscalite } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { FileText, Calculator, Download, Plus, Trash2, Loader2, ChevronDown, ChevronUp, TrendingDown, Scale, User } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');

	let exercices: Fiscalite[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);
	let upgradeRequired = $state(false);
	let generatingCerfa = $state(false);
	let cerfaError = $state('');
	let generatingResume: number | null = $state(null);
	let resumeError = $state('');
	let resumeFiscalData: Map<number, ResumeFiscalData> = $state(new Map());
	let loadingResumeFiscal: number | null = $state(null);
	let downloadingReport2042: string | null = $state(null);
	let showCreateForm = $state(false);
	let creating = $state(false);
	let deletingId: string | null = $state(null);
	let newAnnee = $state(new Date().getFullYear() - 1);
	let newRevenus = $state(0);
	let newCharges = $state(0);
	let showChargeDetail = $state(false);
	let newInteretsEmprunt = $state(0);
	let newTravaux = $state(0);
	let newFraisGestion = $state(0);
	let newAssurance = $state(0);
	let newTaxeFonciere = $state(0);
	let newCopropriete = $state(0);

	const chargeDetailSum = $derived(
		newInteretsEmprunt + newTravaux + newFraisGestion + newAssurance + newTaxeFonciere + newCopropriete
	);
	const hasChargeDetail = $derived(chargeDetailSum > 0);
	const effectiveCharges = $derived(hasChargeDetail ? chargeDetailSum : newCharges);

	const userRole = getContext<string>('userRole');
	const isGerant = $derived(userRole === 'gerant');

	$effect(() => {
		loadFiscalite();
	});

	async function loadFiscalite() {
		loading = true;
		error = null;
		upgradeRequired = false;
		try {
			exercices = await fetchFiscalite(sci.id);
		} catch (err: any) {
			const msg = err?.message ?? '';
			try {
				const parsed = JSON.parse(msg);
				if (parsed.code === 'upgrade_required') {
					upgradeRequired = true;
					return;
				}
			} catch {
				// not JSON, use raw message
			}
			error = 'Impossible de charger la fiscalité.';
		} finally {
			loading = false;
		}
	}

	async function handleLoadResumeFiscal(annee: number) {
		if (resumeFiscalData.has(annee)) return;
		loadingResumeFiscal = annee;
		try {
			const data = await fetchResumeFiscal(sci.id, annee);
			resumeFiscalData = new Map(resumeFiscalData).set(annee, data);
		} catch {
			// Silently fail — the summary card just won't show
		} finally {
			loadingResumeFiscal = null;
		}
	}

	async function handleDownloadReport2042(annee: number, associe: AssocieQuotePart) {
		downloadingReport2042 = associe.associe_id;
		try {
			const blob = await downloadReport2042Pdf(sci.id, annee, associe.associe_id);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `report_2042_${annee}_${associe.nom.replace(/ /g, '_')}.pdf`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de générer le report 2042.', variant: 'error' });
		} finally {
			downloadingReport2042 = null;
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
				siren: sci.siren ?? '',
				regime_fiscal: sci.regime_fiscal ?? undefined
			});
			const url = URL.createObjectURL(blob);
			window.open(url, '_blank');
		} catch (err: any) {
			cerfaError = err?.message ?? 'Erreur lors de la génération du résumé fiscal.';
		} finally {
			generatingCerfa = false;
		}
	}

	async function handleDownloadResumeFiscal(annee: number) {
		generatingResume = annee;
		resumeError = '';
		try {
			const blob = await downloadResumeFiscalPdf(sci.id, annee);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `resume_fiscal_${annee}_${sci.nom}.pdf`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			// Also fetch the JSON summary for the card display
			handleLoadResumeFiscal(annee);
		} catch (err: any) {
			resumeError = err?.message ?? 'Erreur lors de la génération du résumé fiscal détaillé.';
		} finally {
			generatingResume = null;
		}
	}

	function resultatColor(value: number | null | undefined): string {
		if (value == null) return 'text-slate-700 dark:text-slate-300';
		if (value > 0) return 'text-emerald-600 dark:text-emerald-400';
		if (value < 0) return 'text-rose-600 dark:text-rose-400';
		return 'text-slate-700 dark:text-slate-300';
	}

	async function handleCreate() {
		// G11: Check for duplicate fiscal year before submitting
		if (exercices.some((ex) => ex.annee === newAnnee)) {
			addToast({
				title: 'Année déjà existante',
				description: `Un exercice fiscal pour l'année ${newAnnee} existe déjà.`,
				variant: 'error'
			});
			return;
		}
		creating = true;
		try {
			const finalCharges = hasChargeDetail ? chargeDetailSum : newCharges;
			await createFiscalite({
				id_sci: sci.id as string,
				annee: newAnnee,
				total_revenus: newRevenus,
				total_charges: finalCharges,
				...(hasChargeDetail ? {
					interets_emprunt: newInteretsEmprunt,
					travaux: newTravaux,
					frais_gestion: newFraisGestion,
					assurance: newAssurance,
					taxe_fonciere: newTaxeFonciere,
					copropriete: newCopropriete,
				} : {})
			});
			addToast({ title: 'Exercice créé', description: `Exercice ${newAnnee} ajouté.`, variant: 'success' });
			showCreateForm = false;
			newRevenus = 0;
			newCharges = 0;
			newInteretsEmprunt = 0;
			newTravaux = 0;
			newFraisGestion = 0;
			newAssurance = 0;
			newTaxeFonciere = 0;
			newCopropriete = 0;
			showChargeDetail = false;
			await loadFiscalite();
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de créer l\'exercice.', variant: 'error' });
		} finally {
			creating = false;
		}
	}

	async function handleDelete(ex: Fiscalite) {
		if (!ex.id) return;
		deletingId = String(ex.id);
		try {
			await deleteFiscalite(ex.id);
			addToast({ title: 'Exercice supprimé', description: `Exercice ${ex.annee} supprimé.`, variant: 'success' });
			await loadFiscalite();
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de supprimer.', variant: 'error' });
		} finally {
			deletingId = null;
		}
	}
</script>

<svelte:head><title>Fiscalité | {sci.nom} | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<h1 class="sci-page-title">Fiscalité</h1>
	</header>

	{#if upgradeRequired}
		<div class="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center dark:border-amber-800 dark:bg-amber-950/30">
			<p class="text-lg font-semibold text-amber-800 dark:text-amber-200">Fonctionnalité Pro</p>
			<p class="mt-2 text-sm text-amber-700 dark:text-amber-300">
				La fiscalité et la génération du résumé fiscal sont disponibles avec le plan Pro.
			</p>
			<a
				href="/pricing"
				class="mt-4 inline-block rounded-lg bg-sky-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-sky-700"
			>
				Voir les offres
			</a>
		</div>
	{:else}

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

	<!-- Résumé fiscal PDF Generation -->
	{#if sci.regime_fiscal === 'is' || sci.regime_fiscal === 'IS'}
		<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center gap-2">
				<FileText class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
					Déclaration fiscale
				</h2>
			</div>
			<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
				Les SCI à l'IS utilisent la liasse fiscale 2065 (hors périmètre).
			</p>
		</div>
	{:else}
	<div
		class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
	>
		<div class="flex items-center gap-2">
			<FileText class="h-5 w-5 text-sky-600 dark:text-sky-400" />
			<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
				Résumé fiscal PDF
			</h2>
		</div>
		<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
			Générez un résumé simplifié de votre déclaration des revenus fonciers au format PDF.
		</p>

		<p class="mt-2 text-xs text-amber-600 dark:text-amber-400">
			⚠ Résultat simplifié (revenus − charges). Ne tient pas compte des abattements micro-foncier, amortissements ou reports déficitaires. Consultez votre comptable pour la déclaration officielle.
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
						<div class="flex items-center gap-2">
							<button
								class="inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-white px-3 py-1.5 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-50 disabled:opacity-50 dark:border-emerald-800 dark:bg-slate-900 dark:text-emerald-400 dark:hover:bg-slate-800"
								disabled={loadingResumeFiscal === ex.annee}
								onclick={() => handleLoadResumeFiscal(ex.annee)}
							>
								<Scale class="h-3.5 w-3.5" />
								{#if loadingResumeFiscal === ex.annee}
									Chargement…
								{:else if resumeFiscalData.has(ex.annee)}
									Analyse affichée
								{:else}
									Analyser
								{/if}
							</button>
							<button
								class="inline-flex items-center gap-1.5 rounded-lg border border-sky-200 bg-white px-3 py-1.5 text-sm font-medium text-sky-700 transition-colors hover:bg-sky-50 disabled:opacity-50 dark:border-sky-800 dark:bg-slate-900 dark:text-sky-400 dark:hover:bg-slate-800"
								disabled={generatingResume === ex.annee}
								onclick={() => handleDownloadResumeFiscal(ex.annee)}
							>
								<FileText class="h-3.5 w-3.5" />
								{generatingResume === ex.annee ? 'Génération…' : 'Résumé détaillé'}
							</button>
							<button
								class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
								disabled={generatingCerfa}
								onclick={() => handleGenerateCerfa(ex)}
							>
								<Download class="h-3.5 w-3.5" />
								{generatingCerfa ? 'Génération…' : 'Résumé fiscal PDF'}
							</button>
						</div>
					</div>
				{/each}
			</div>
		{:else if !loading}
			<p class="mt-4 text-sm text-slate-500 dark:text-slate-400">
				Ajoutez un exercice fiscal pour pouvoir générer le résumé fiscal PDF.
			</p>
		{/if}

		{#if cerfaError}
			<p class="mt-3 text-sm text-rose-600 dark:text-rose-400">{cerfaError}</p>
		{/if}
		{#if resumeError}
			<p class="mt-3 text-sm text-rose-600 dark:text-rose-400">{resumeError}</p>
		{/if}
	</div>
	{/if}

	<!-- Résumé fiscal summary cards -->
	{#each [...resumeFiscalData.entries()] as [annee, rf] (annee)}
		<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center gap-2 mb-4">
				<Scale class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
					Analyse fiscale {annee}
				</h2>
			</div>

			<div class="grid gap-4 sm:grid-cols-2">
				<!-- Régime recommandé -->
				<div class="rounded-xl border border-slate-100 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-900/50">
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400 mb-2">
						Régime recommandé
					</p>
					<span class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold {rf.regime_recommande === 'reel' ? 'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300' : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'}">
						{rf.regime_recommande === 'reel' ? 'Régime réel' : 'Micro-foncier'}
					</span>
					{#if rf.micro_foncier_eligible && rf.economie_regime_recommande > 0}
						<p class="mt-2 text-sm text-emerald-700 dark:text-emerald-400">
							Économie de {formatEur(rf.economie_regime_recommande)} en optant pour le {rf.regime_recommande === 'reel' ? 'régime réel' : 'micro-foncier'}
						</p>
					{/if}
					{#if !rf.micro_foncier_eligible}
						<p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
							Revenus bruts > 15 000 EUR — micro-foncier non éligible
						</p>
					{/if}
				</div>

				<!-- Déficit foncier -->
				{#if rf.is_deficit}
					<div class="rounded-xl border border-rose-100 bg-rose-50/50 p-4 dark:border-rose-900/50 dark:bg-rose-950/20">
						<div class="flex items-center gap-1.5 mb-2">
							<TrendingDown class="h-4 w-4 text-rose-600 dark:text-rose-400" />
							<p class="text-xs font-medium text-rose-600 uppercase dark:text-rose-400">
								Déficit foncier
							</p>
						</div>
						<p class="text-lg font-bold text-rose-700 dark:text-rose-300">
							{formatEur(rf.deficit_total)}
						</p>
						{#if rf.deficit_imputable_revenu_global > 0}
							<p class="mt-1 text-sm text-slate-700 dark:text-slate-300">
								Dont {formatEur(rf.deficit_imputable_revenu_global)} imputable sur le revenu global
								<span class="text-xs text-slate-500">(max 10 700 EUR)</span>
							</p>
						{/if}
						{#if rf.deficit_interets_emprunt > 0}
							<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
								Intérêts d'emprunt : {formatEur(rf.deficit_interets_emprunt)} (reportable revenus fonciers uniquement)
							</p>
						{/if}
						{#if rf.deficit_reportable_foncier > 0}
							<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
								Excédent reportable : {formatEur(rf.deficit_reportable_foncier)} sur 10 ans
							</p>
						{/if}
					</div>
				{:else}
					<div class="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/20">
						<p class="text-xs font-medium text-emerald-600 uppercase dark:text-emerald-400 mb-2">
							Résultat fiscal net
						</p>
						<p class="text-lg font-bold text-emerald-700 dark:text-emerald-300">
							{formatEur(rf.resultat_global)}
						</p>
						<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
							Bénéfice foncier imposable
						</p>
					</div>
				{/if}
			</div>

			<!-- Associé quote-parts with report 2042 buttons -->
			{#if rf.associes && rf.associes.length > 0}
				<div class="mt-4">
					<div class="flex items-center gap-1.5 mb-3">
						<User class="h-4 w-4 text-sky-600 dark:text-sky-400" />
						<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">
							Quote-parts des associés — Cases 2042
						</p>
					</div>
					<div class="space-y-2">
						{#each rf.associes as associe (associe.associe_id)}
							<div class="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/50 px-4 py-2.5 dark:border-slate-800 dark:bg-slate-900/50">
								<div class="flex-1 min-w-0">
									<span class="font-medium text-slate-900 dark:text-slate-100">{associe.nom}</span>
									<span class="ml-2 text-sm text-slate-500">{associe.part_pct.toFixed(1)} %</span>
									<span class="ml-2 text-sm font-semibold {resultatColor(associe.quote_part_resultat)}">
										{formatEur(associe.quote_part_resultat)}
									</span>
									{#if associe.case_4ba > 0}
										<span class="ml-2 text-xs text-emerald-600 dark:text-emerald-400">4BA: {formatEur(associe.case_4ba)}</span>
									{/if}
									{#if associe.case_4bb > 0}
										<span class="ml-2 text-xs text-rose-600 dark:text-rose-400">4BB: {formatEur(associe.case_4bb)}</span>
									{/if}
									{#if associe.case_4bc > 0}
										<span class="ml-2 text-xs text-rose-600 dark:text-rose-400">4BC: {formatEur(associe.case_4bc)}</span>
									{/if}
								</div>
								<button
									class="ml-3 inline-flex items-center gap-1.5 rounded-lg border border-sky-200 bg-white px-3 py-1.5 text-xs font-medium text-sky-700 transition-colors hover:bg-sky-50 disabled:opacity-50 dark:border-sky-800 dark:bg-slate-900 dark:text-sky-400 dark:hover:bg-slate-800"
									disabled={downloadingReport2042 === associe.associe_id}
									onclick={() => handleDownloadReport2042(annee, associe)}
								>
									<Download class="h-3 w-3" />
									{downloadingReport2042 === associe.associe_id ? 'PDF...' : 'Report 2042'}
								</button>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	{/each}

	<!-- Exercices fiscaux -->
	<div
		class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
	>
		<div class="mb-4 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<FileText class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
					Exercices fiscaux
				</h2>
			</div>
			{#if isGerant && !upgradeRequired}
				<button
					onclick={() => { showCreateForm = !showCreateForm; }}
					class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
				>
					<Plus class="h-4 w-4" />
					Ajouter
				</button>
			{/if}
		</div>

		{#if showCreateForm}
			<div class="mb-4 rounded-xl border border-sky-200 bg-sky-50/50 p-4 dark:border-sky-800 dark:bg-sky-950/20">
				<p class="mb-3 text-sm font-medium text-slate-900 dark:text-slate-100">Nouvel exercice fiscal</p>
				<div class="grid gap-3 sm:grid-cols-3">
					<div>
						<label for="new-annee" class="block text-xs font-medium text-slate-500 uppercase">Année</label>
						<input
							id="new-annee"
							type="number"
							min="2000"
							max="2100"
							bind:value={newAnnee}
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
					<div>
						<label for="new-revenus" class="block text-xs font-medium text-slate-500 uppercase">Revenus bruts</label>
						<input
							id="new-revenus"
							type="number"
							min="0"
							step="0.01"
							bind:value={newRevenus}
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
					<div>
						<label for="new-charges" class="block text-xs font-medium text-slate-500 uppercase">Charges déductibles</label>
						<input
							id="new-charges"
							type="number"
							min="0"
							step="0.01"
							bind:value={newCharges}
							class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
						/>
					</div>
				</div>

				<!-- Collapsible charge decomposition -->
				<div class="mt-3">
					<button
						type="button"
						onclick={() => { showChargeDetail = !showChargeDetail; }}
						class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
					>
						{#if showChargeDetail}
							<ChevronUp class="h-4 w-4" />
						{:else}
							<ChevronDown class="h-4 w-4" />
						{/if}
						Détail des charges
					</button>

					{#if showChargeDetail}
						<div class="mt-3 rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
							<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
								<div>
									<label for="new-interets" class="block text-xs font-medium text-slate-500 uppercase">Intérêts d'emprunt</label>
									<input id="new-interets" type="number" min="0" step="0.01" bind:value={newInteretsEmprunt} class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" />
								</div>
								<div>
									<label for="new-travaux" class="block text-xs font-medium text-slate-500 uppercase">Travaux</label>
									<input id="new-travaux" type="number" min="0" step="0.01" bind:value={newTravaux} class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" />
								</div>
								<div>
									<label for="new-frais-gestion" class="block text-xs font-medium text-slate-500 uppercase">Frais de gestion</label>
									<input id="new-frais-gestion" type="number" min="0" step="0.01" bind:value={newFraisGestion} class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" />
								</div>
								<div>
									<label for="new-assurance" class="block text-xs font-medium text-slate-500 uppercase">Assurance</label>
									<input id="new-assurance" type="number" min="0" step="0.01" bind:value={newAssurance} class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" />
								</div>
								<div>
									<label for="new-taxe-fonciere" class="block text-xs font-medium text-slate-500 uppercase">Taxe foncière</label>
									<input id="new-taxe-fonciere" type="number" min="0" step="0.01" bind:value={newTaxeFonciere} class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" />
								</div>
								<div>
									<label for="new-copropriete" class="block text-xs font-medium text-slate-500 uppercase">Copropriété</label>
									<input id="new-copropriete" type="number" min="0" step="0.01" bind:value={newCopropriete} class="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" />
								</div>
							</div>
							{#if hasChargeDetail}
								<p class="mt-3 text-sm text-slate-600 dark:text-slate-400">
									Total charges (auto-calculé) : <span class="font-semibold text-rose-700 dark:text-rose-400">{formatEur(chargeDetailSum)}</span>
								</p>
							{/if}
						</div>
					{/if}
				</div>

				<div class="mt-3 flex items-center justify-between">
					<p class="text-sm text-slate-500 dark:text-slate-400">
						Résultat : <span class="font-semibold {resultatColor(newRevenus - effectiveCharges)}">{formatEur(newRevenus - effectiveCharges)}</span>
					</p>
					<div class="flex gap-2">
						<button
							onclick={() => { showCreateForm = false; }}
							class="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
						>
							Annuler
						</button>
						<button
							onclick={handleCreate}
							disabled={creating}
							class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
						>
							{#if creating}
								<Loader2 class="h-4 w-4 animate-spin" />
							{/if}
							Créer
						</button>
					</div>
				</div>
			</div>
		{/if}

		{#if loading}
			<div class="sci-loading" aria-label="Chargement"></div>
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
			<div class="sci-fade-in-up overflow-x-auto">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-slate-200 dark:border-slate-700">
							<th
								class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
							>
								Année
							</th>
							<th
								class="pb-3 pr-4 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
							>
								Revenus
							</th>
							<th
								class="pb-3 pr-4 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
							>
								Charges
							</th>
							<th
								class="pb-3 text-right text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase"
							>
								Résultat fiscal
							</th>
							{#if isGerant}
								<th class="pb-3 w-10"></th>
							{/if}
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
									{ex.resultat_fiscal != null ? formatEur(ex.resultat_fiscal) : '—'}
								</td>
								{#if isGerant}
									<td class="py-3 text-right">
										<button
											onclick={() => handleDelete(ex)}
											disabled={deletingId === String(ex.id)}
											class="text-slate-400 transition-colors hover:text-rose-600 disabled:opacity-50 dark:hover:text-rose-400"
											title="Supprimer cet exercice"
										>
											{#if deletingId === String(ex.id)}
												<Loader2 class="h-4 w-4 animate-spin" />
											{:else}
												<Trash2 class="h-4 w-4" />
											{/if}
										</button>
									</td>
								{/if}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
	{/if}
</section>
