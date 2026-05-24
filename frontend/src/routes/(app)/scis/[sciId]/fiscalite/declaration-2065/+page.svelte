<script lang="ts">
	import { page } from '$app/state';
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';
	import { generateDeclaration2065, downloadDeclaration2065Pdf, type Declaration2065 } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { FileText, Calculator, Download, Loader2, AlertTriangle } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');

	let sciId = $derived(page.params.sciId!);
	let annee = $state(new Date().getFullYear() - 1);
	let loading = $state(false);
	let downloading = $state(false);
	let declaration: Declaration2065 | null = $state(null);
	let error: string | null = $state(null);

	async function handleGenerate() {
		loading = true;
		error = null;
		declaration = null;
		try {
			declaration = await generateDeclaration2065(sciId, { exercice: annee });
			addToast({ title: 'Déclaration 2065 générée', variant: 'success' });
		} catch (err: any) {
			error = err?.message ?? 'Impossible de générer la déclaration.';
			addToast({ title: error as string, variant: 'error' });
		} finally {
			loading = false;
		}
	}

	async function handleDownloadPdf() {
		if (!declaration) return;
		downloading = true;
		try {
			const blob = await downloadDeclaration2065Pdf(sciId, annee);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `declaration_2065_${annee}_${sci.nom.replace(/\s+/g, '_')}.pdf`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			addToast({ title: 'PDF téléchargé', variant: 'success' });
		} catch (err: any) {
			addToast({ title: err?.message ?? 'Erreur de téléchargement', variant: 'error' });
		} finally {
			downloading = false;
		}
	}

	function bilanItems(bilan: any): Array<{ label: string; value: number }> {
		const libelles: Record<string, string> = {
			immobilisations: 'Immobilisations',
			travaux_en_cours: 'Travaux en cours',
			creances_clients: 'Créances clients',
			tresorerie: 'Trésorerie',
			capital_social: 'Capital social',
			reserves: 'Réserves',
			resultat: 'Résultat de l\'exercice',
			emprunts: 'Emprunts',
			fournisseurs: 'Dettes fournisseurs',
			autres_dettes: 'Autres dettes',
		};
		return Object.entries(bilan)
			.filter(([, v]) => v != null && v !== 0)
			.map(([k, v]) => ({
				label: libelles[k] ?? k,
				value: v as number
			}))
			.sort((a, b) => b.value - a.value);
	}

	function bilanTotal(bilan: any): number {
		return Object.values(bilan)
			.filter((v): v is number => v != null)
			.reduce((sum, v) => sum + v, 0);
	}
</script>

<svelte:head><title>Déclaration 2065 | {sci.nom} | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<div class="flex items-center justify-between">
			<h1 class="sci-page-title">Déclaration 2065</h1>
		</div>
		<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
			Générez la liasse fiscale 2065 (bilan actif/passif) pour votre SCI à l'IS.
		</p>
	</header>

	<!-- Formulaire -->
	<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="flex items-center gap-2">
			<Calculator class="h-5 w-5 text-sky-600 dark:text-sky-400" />
			<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
				Exercice fiscal
			</h2>
		</div>

		<div class="mt-4 flex flex-wrap items-end gap-4">
			<div>
				<label for="exercice-annee" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
					Année de clôture
				</label>
				<input
					id="exercice-annee"
					type="number"
					bind:value={annee}
					min="2000"
					max="2100"
					class="w-32 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
				/>
			</div>
			<button
				class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
				disabled={loading}
				onclick={handleGenerate}
			>
				{#if loading}
					<Loader2 class="h-4 w-4 animate-spin" />
					Génération…
				{:else}
					<FileText class="h-4 w-4" />
					Générer la déclaration
				{/if}
			</button>
		</div>
	</div>

	<!-- Erreur -->
	{#if error}
		<div class="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-800 dark:bg-rose-950/30">
			<div class="flex items-center gap-2">
				<AlertTriangle class="h-5 w-5 text-rose-600 dark:text-rose-400" />
				<p class="text-sm font-medium text-rose-700 dark:text-rose-300">{error}</p>
			</div>
		</div>
	{/if}

	<!-- Résultat -->
	{#if declaration}
		<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
			<div class="mb-4 flex items-center justify-between">
				<div class="flex items-center gap-2">
					<FileText class="h-5 w-5 text-sky-600 dark:text-sky-400" />
					<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
						Bilan — Exercice {declaration.exercice}
					</h2>
				</div>
				<button
					class="inline-flex items-center gap-2 rounded-lg border border-sky-200 bg-white px-4 py-2 text-sm font-medium text-sky-700 transition-colors hover:bg-sky-50 disabled:opacity-50 dark:border-sky-800 dark:bg-slate-900 dark:text-sky-400 dark:hover:bg-slate-800"
					disabled={downloading}
					onclick={handleDownloadPdf}
				>
					{#if downloading}
						<Loader2 class="h-4 w-4 animate-spin" />
						Téléchargement…
					{:else}
						<Download class="h-4 w-4" />
						Télécharger le PDF
					{/if}
				</button>
			</div>

			<!-- Écart d'équilibre -->
			{#if declaration.ecart !== 0}
				<div class="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-950/30">
					<p class="text-sm text-amber-700 dark:text-amber-300">
						⚠ Bilan déséquilibré : écart de {formatEur(declaration.ecart)}. Vérifiez les données du bien et du crédit.
					</p>
				</div>
			{/if}

			<div class="grid gap-6 lg:grid-cols-2">
				<!-- Actif -->
				<div class="rounded-xl border border-slate-200 p-4 dark:border-slate-700">
					<h3 class="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
						Bilan Actif
					</h3>
					{#each bilanItems(declaration.actif) as item}
						<div class="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800 last:border-0">
							<span class="text-sm text-slate-700 dark:text-slate-300">{item.label}</span>
							<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{formatEur(item.value)}</span>
						</div>
					{/each}
					<div class="mt-2 flex items-center justify-between border-t border-slate-300 pt-2 dark:border-slate-600">
						<span class="text-sm font-semibold text-slate-900 dark:text-slate-100">Total Actif</span>
						<span class="text-sm font-bold text-slate-900 dark:text-slate-100">{formatEur(bilanTotal(declaration.actif))}</span>
					</div>
				</div>

				<!-- Passif -->
				<div class="rounded-xl border border-slate-200 p-4 dark:border-slate-700">
					<h3 class="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
						Bilan Passif
					</h3>
					{#each bilanItems(declaration.passif) as item}
						<div class="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800 last:border-0">
							<span class="text-sm text-slate-700 dark:text-slate-300">{item.label}</span>
							<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{formatEur(item.value)}</span>
						</div>
					{/each}
					<div class="mt-2 flex items-center justify-between border-t border-slate-300 pt-2 dark:border-slate-600">
						<span class="text-sm font-semibold text-slate-900 dark:text-slate-100">Total Passif</span>
						<span class="text-sm font-bold text-slate-900 dark:text-slate-100">{formatEur(bilanTotal(declaration.passif))}</span>
					</div>
				</div>
			</div>
		</div>
	{/if}
</section>
