<script lang="ts">
	import type { FicheBien } from '$lib/api';
	import { FileText, Pencil } from 'lucide-svelte';

	interface Props {
		bien: FicheBien;
		sciNom: string;
		isGerant: boolean;
	}

	let { bien, sciNom, isGerant }: Props = $props();

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
		vacant: { label: 'Vacant', class: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300' },
		travaux: { label: 'Travaux', class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' }
	};

	let bailStatut = $derived(bien.bail_actif?.statut ?? 'vacant');
	let statutInfo = $derived(statutLabels[bailStatut] ?? statutLabels['vacant']);
</script>

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
					class="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
				>
					<Pencil class="h-4 w-4" />
					Modifier
				</button>
				<button
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				>
					<FileText class="h-4 w-4" />
					Générer quittance
				</button>
			</div>
		{/if}
	</div>

	<div class="mt-3 flex flex-wrap gap-2">
		{#if bien.type_bien}
			<span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
				{bien.type_bien}
			</span>
		{/if}

		{#if bien.dpe_classe}
			<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold {dpeColors[bien.dpe_classe.toUpperCase()] ?? 'bg-slate-200 text-slate-700'}">
				DPE {bien.dpe_classe.toUpperCase()}
			</span>
		{/if}

		<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {statutInfo.class}">
			{statutInfo.label}
		</span>
	</div>
</header>
