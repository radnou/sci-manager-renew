<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail, DocumentBienEmbed, Bien } from '$lib/api';
	import { fetchSciBiens, fetchBienDocuments } from '$lib/api';
	import { formatFrDate } from '$lib/high-value/formatters';
	import { FileText, Download, FolderOpen } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');
	const sciId = getContext<string>('sciId');

	type BienDocs = {
		bien: Bien;
		documents: DocumentBienEmbed[];
	};

	let groups: BienDocs[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);

	const categorieLabels: Record<string, string> = {
		bail: 'Bail',
		quittance: 'Quittance',
		diagnostic: 'Diagnostic',
		assurance: 'Assurance',
		autre: 'Autre'
	};

	const categorieBadgeColors: Record<string, string> = {
		bail: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
		quittance: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
		diagnostic: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
		assurance: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
		autre: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
	};

	$effect(() => {
		loadDocuments();
	});

	async function loadDocuments() {
		loading = true;
		error = null;
		try {
			const biens = await fetchSciBiens(sciId);
			const result: BienDocs[] = [];
			for (const bien of biens) {
				const docs = await fetchBienDocuments(sciId, bien.id!);
				result.push({ bien, documents: docs });
			}
			groups = result;
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger les documents.';
		} finally {
			loading = false;
		}
	}

	let totalDocs = $derived(groups.reduce((sum, g) => sum + g.documents.length, 0));
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<h1 class="sci-page-title">Documents</h1>
	</header>

	{#if loading}
		<div class="mt-6 space-y-4">
			{#each Array.from({ length: 3 }) as _}
				<div class="h-32 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
			{/each}
		</div>
	{:else if error}
		<div
			class="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30"
		>
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={loadDocuments}
				class="mt-3 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				Réessayer
			</button>
		</div>
	{:else if totalDocs === 0}
		<div
			class="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-16 dark:border-slate-700"
		>
			<FolderOpen class="mb-3 h-12 w-12 text-slate-300 dark:text-slate-600" />
			<p class="text-sm text-slate-500 dark:text-slate-400">
				Aucun document pour cette SCI.
			</p>
			<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
				Ajoutez des documents depuis la fiche de chaque bien.
			</p>
		</div>
	{:else}
		<div class="mt-6 space-y-6">
			{#each groups as group}
				{#if group.documents.length > 0}
					<div
						class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
					>
						<h2 class="mb-4 flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
							<FileText class="h-5 w-5 text-sky-600 dark:text-sky-400" />
							{group.bien.adresse}
							{#if group.bien.ville}
								<span class="text-sm font-normal text-slate-500">
									— {group.bien.ville}
								</span>
							{/if}
						</h2>

						<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
							{#each group.documents as doc (doc.id)}
								<div
									class="flex items-start justify-between rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
								>
									<div class="min-w-0 flex-1">
										<p class="text-sm font-medium text-slate-900 dark:text-slate-100">
											{doc.nom}
										</p>
										<div class="mt-1 flex items-center gap-2">
											<span
												class="rounded-full px-2 py-0.5 text-[0.65rem] font-semibold {categorieBadgeColors[doc.categorie] ?? categorieBadgeColors['autre']}"
											>
												{categorieLabels[doc.categorie] ?? doc.categorie}
											</span>
											<span class="text-xs text-slate-400 dark:text-slate-500">
												{formatFrDate(doc.created_at)}
											</span>
										</div>
									</div>
									<a
										href={doc.url}
										target="_blank"
										rel="noopener noreferrer"
										class="ml-2 inline-flex shrink-0 items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"
									>
										<Download class="h-3 w-3" />
										Ouvrir
									</a>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			{/each}
		</div>
	{/if}
</section>
