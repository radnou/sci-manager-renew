<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail, DocumentBienEmbed, Bien, SciDocumentItem } from '$lib/api';
	import { fetchSciDocuments, uploadDocumentBien, deleteDocumentBien, fetchSciBiens } from '$lib/api';
	import { formatFrDate } from '$lib/high-value/formatters';
	import { addToast } from '$lib/components/ui/toast';
	import { FileText, Download, FolderOpen, Upload, Trash2, Loader2, Plus } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');
	const sciId = getContext<string>('sciId');
	const userRole = getContext<string>('userRole');
	const isGerant = $derived(userRole === 'gerant');

	// Upload state
	let showUploadForm = $state(false);
	let uploadBienId = $state<string | number | null>(null);
	let uploadFile: File | null = $state(null);
	let uploadNom = $state('');
	let uploadCategorie = $state('autre');
	let uploading = $state(false);

	// Delete state
	let deletingDocId: number | null = $state(null);

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
			// Single API call instead of N+1
			const allDocs = await fetchSciDocuments(sciId);
			// Group by id_bien
			const byBien = new Map<string, SciDocumentItem[]>();
			for (const doc of allDocs) {
				const key = String(doc.id_bien);
				if (!byBien.has(key)) byBien.set(key, []);
				byBien.get(key)!.push(doc);
			}
			groups = Array.from(byBien.entries()).map(([bienId, docs]) => ({
				bien: { id: bienId, adresse: docs[0]?.bien_adresse ?? bienId } as Bien,
				documents: docs as unknown as DocumentBienEmbed[],
			}));
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger les documents.';
		} finally {
			loading = false;
		}
	}

	let totalDocs = $derived(groups.reduce((sum, g) => sum + g.documents.length, 0));

	function openUploadForm(bienId: string | number) {
		uploadBienId = bienId;
		uploadFile = null;
		uploadNom = '';
		uploadCategorie = 'autre';
		showUploadForm = true;
	}

	function handleFileSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		if (input.files?.[0]) {
			uploadFile = input.files[0];
			if (!uploadNom) uploadNom = uploadFile.name;
		}
	}

	async function handleUpload() {
		if (!uploadFile || !uploadBienId || !uploadNom.trim()) return;
		uploading = true;
		try {
			await uploadDocumentBien(sciId, uploadBienId, uploadFile, uploadNom.trim(), uploadCategorie);
			addToast({ title: 'Document ajouté', description: `${uploadNom} a été uploadé.`, variant: 'success' });
			showUploadForm = false;
			await loadDocuments();
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? "Impossible d'uploader le document.", variant: 'error' });
		} finally {
			uploading = false;
		}
	}

	async function handleDeleteDoc(bienId: string | number, doc: DocumentBienEmbed) {
		if (!confirm(`Supprimer le document "${doc.nom}" ?`)) return;
		deletingDocId = doc.id;
		try {
			await deleteDocumentBien(sciId, bienId, doc.id);
			addToast({ title: 'Document supprimé', description: `${doc.nom} a été supprimé.`, variant: 'success' });
			await loadDocuments();
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de supprimer le document.', variant: 'error' });
		} finally {
			deletingDocId = null;
		}
	}
</script>

<svelte:head><title>Documents | {sci.nom} | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<div class="flex items-center justify-between">
			<h1 class="sci-page-title">Documents</h1>
		</div>
	</header>

	{#if loading}
		<div class="sci-loading" aria-label="Chargement"></div>
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
	{:else if totalDocs === 0 && groups.every(g => g.documents.length === 0) && !isGerant}
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
		<div class="sci-stagger mt-6 space-y-6">
			{#each groups as group}
				{#if group.documents.length > 0 || isGerant}
					<div
						class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
					>
						<div class="mb-4 flex items-center justify-between">
							<h2 class="flex items-center gap-2 text-base font-semibold text-slate-900 dark:text-slate-100">
								<FileText class="h-5 w-5 text-sky-600 dark:text-sky-400" />
								{group.bien.adresse}
								{#if group.bien.ville}
									<span class="text-sm font-normal text-slate-500">
										— {group.bien.ville}
									</span>
								{/if}
							</h2>
							{#if isGerant}
								<button
									onclick={() => openUploadForm(group.bien.id!)}
									class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
								>
									<Upload class="h-3.5 w-3.5" />
									Ajouter
								</button>
							{/if}
						</div>

						{#if group.documents.length > 0}
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
												class="rounded-full px-2 py-0.5 text-xs font-semibold {categorieBadgeColors[doc.categorie] ?? categorieBadgeColors['autre']}"
											>
												{categorieLabels[doc.categorie] ?? doc.categorie}
											</span>
											<span class="text-xs text-slate-400 dark:text-slate-500">
												{formatFrDate(doc.created_at)}
											</span>
										</div>
									</div>
									<div class="ml-2 flex shrink-0 items-center gap-1">
										<a
											href={doc.url}
											target="_blank"
											rel="noopener noreferrer"
											class="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"
										>
											<Download class="h-3 w-3" />
											Ouvrir
										</a>
										{#if isGerant}
											<button
												onclick={() => handleDeleteDoc(group.bien.id!, doc)}
												disabled={deletingDocId === doc.id}
												class="inline-flex items-center rounded-md border border-slate-200 bg-white p-1 text-slate-400 transition-colors hover:border-rose-200 hover:text-rose-600 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-rose-800 dark:hover:text-rose-400"
												title="Supprimer ce document"
											>
												{#if deletingDocId === doc.id}
													<Loader2 class="h-3.5 w-3.5 animate-spin" />
												{:else}
													<Trash2 class="h-3.5 w-3.5" />
												{/if}
											</button>
										{/if}
									</div>
								</div>
							{/each}
						</div>
						{:else}
							<p class="text-sm text-slate-400 dark:text-slate-500">Aucun document pour ce bien.</p>
						{/if}
					</div>
				{/if}
			{/each}
		</div>
	{/if}

	<!-- Upload Document Modal -->
	{#if showUploadForm}
		<div
			role="dialog"
			aria-modal="true"
			aria-labelledby="upload-doc-title"
			class="fixed inset-0 z-50 flex items-center justify-center p-4"
		>
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick={() => { if (!uploading) showUploadForm = false; }}></div>
			<form
				class="relative w-full max-w-[480px] rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900"
				onsubmit={(e) => { e.preventDefault(); handleUpload(); }}
			>
				<div class="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
					<h2 id="upload-doc-title" class="text-base font-semibold text-slate-900 dark:text-slate-100">Ajouter un document</h2>
				</div>
				<div class="space-y-4 px-5 py-4">
					<div>
						<label for="upload-file" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Fichier</label>
						<input id="upload-file" type="file" onchange={handleFileSelect} required
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm file:mr-3 file:rounded-md file:border-0 file:bg-sky-50 file:px-3 file:py-1 file:text-xs file:font-medium file:text-sky-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:file:bg-sky-900/40 dark:file:text-sky-300" />
					</div>
					<div>
						<label for="upload-nom" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Nom du document</label>
						<input id="upload-nom" type="text" bind:value={uploadNom} required placeholder="Ex: Bail signé 2025"
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
					</div>
					<div>
						<label for="upload-categorie" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Catégorie</label>
						<select id="upload-categorie" bind:value={uploadCategorie}
							class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
							<option value="bail">Bail</option>
							<option value="quittance">Quittance</option>
							<option value="diagnostic">Diagnostic</option>
							<option value="assurance">Assurance</option>
							<option value="autre">Autre</option>
						</select>
					</div>
				</div>
				<div class="flex items-center justify-end gap-2 border-t border-slate-200 px-5 py-3 dark:border-slate-700">
					<button type="button" onclick={() => { showUploadForm = false; }} disabled={uploading}
						class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800">
						Annuler
					</button>
					<button type="submit" disabled={uploading || !uploadFile}
						class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50">
						{#if uploading}<Loader2 class="h-4 w-4 animate-spin" />{/if}
						Uploader
					</button>
				</div>
			</form>
		</div>
	{/if}
</section>
