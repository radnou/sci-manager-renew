<script lang="ts">
	import type { DocumentBienEmbed } from '$lib/api';
	import { uploadDocumentBien, deleteDocumentBien } from '$lib/api';
	import { formatFrDate } from '$lib/high-value/formatters';
	import { FileText, Upload, Trash2, Download } from 'lucide-svelte';
	import { addToast } from '$lib/components/ui/toast/toast-store';

	interface Props {
		documents: DocumentBienEmbed[];
		isGerant: boolean;
		sciId: string;
		bienId: string | number;
	}

	let { documents, isGerant, sciId, bienId }: Props = $props();

	let showUploadForm = $state(false);
	let uploadNom = $state('');
	let uploadCategorie = $state('autre');
	let uploadFile: File | null = $state(null);
	let uploading = $state(false);
	let uploadError: string | null = $state(null);

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

	function getCategorieLabel(cat: string): string {
		return categorieLabels[cat] ?? cat;
	}

	function getCategorieBadge(cat: string): string {
		return categorieBadgeColors[cat] ?? categorieBadgeColors['autre'];
	}

	function handleFileChange(e: Event) {
		const target = e.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			uploadFile = target.files[0];
			if (!uploadNom) {
				uploadNom = uploadFile.name.replace(/\.[^/.]+$/, '');
			}
		}
	}

	async function handleUpload() {
		if (!uploadFile || !uploadNom.trim()) return;

		uploading = true;
		uploadError = null;
		try {
			const doc = await uploadDocumentBien(sciId, bienId, uploadFile, uploadNom.trim(), uploadCategorie);
			documents = [doc, ...documents];
			showUploadForm = false;
			uploadNom = '';
			uploadCategorie = 'autre';
			uploadFile = null;
		} catch (err: any) {
			addToast({ title: err?.message ?? "Erreur lors de l'upload", variant: 'error' });
		} finally {
			uploading = false;
		}
	}

	function handleDelete(docId: number) {
		addToast({
			title: 'Document supprimé',
			variant: 'undo',
			undoCallbacks: {
				onUndo: () => {},
				onExpire: async () => {
					try {
						await deleteDocumentBien(sciId, bienId, docId);
						documents = documents.filter((d) => d.id !== docId);
					} catch (err: any) {
						addToast({ title: err?.message ?? 'Erreur lors de la suppression', variant: 'error' });
					}
				}
			}
		});
	}
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center justify-between">
		<div class="flex items-center gap-2">
			<FileText class="h-5 w-5 text-sky-600 dark:text-sky-400" />
			<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Documents</h2>
		</div>
		{#if isGerant}
			<button
				onclick={() => (showUploadForm = !showUploadForm)}
				class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
			>
				<Upload class="h-4 w-4" />
				Ajouter
			</button>
		{/if}
	</div>

	<!-- Upload form -->
	{#if showUploadForm && isGerant}
		<div
			class="mb-4 rounded-xl border border-sky-200 bg-sky-50 p-4 dark:border-sky-800 dark:bg-sky-950/20"
		>
			<div class="grid gap-3 sm:grid-cols-2">
				<div>
					<label for="doc-file" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
						Fichier
					</label>
					<input
						id="doc-file"
						type="file"
						onchange={handleFileChange}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
					/>
				</div>
				<div>
					<label for="doc-nom" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
						Nom
					</label>
					<input
						id="doc-nom"
						type="text"
						bind:value={uploadNom}
						placeholder="Nom du document"
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
					/>
				</div>
				<div>
					<label for="doc-cat" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
						Catégorie
					</label>
					<select
						id="doc-cat"
						bind:value={uploadCategorie}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
					>
						<option value="bail">Bail</option>
						<option value="quittance">Quittance</option>
						<option value="diagnostic">Diagnostic</option>
						<option value="assurance">Assurance</option>
						<option value="autre">Autre</option>
					</select>
				</div>
				<div class="flex items-end">
					<button
						onclick={handleUpload}
						disabled={uploading || !uploadFile || !uploadNom.trim()}
						class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
					>
						{#if uploading}
							Envoi...
						{:else}
							<Upload class="h-4 w-4" />
							Envoyer
						{/if}
					</button>
				</div>
			</div>
			{#if uploadError}
				<p class="mt-2 text-xs text-rose-600 dark:text-rose-400">{uploadError}</p>
			{/if}
		</div>
	{/if}

	<!-- Document list -->
	{#if documents.length === 0}
		<div
			class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
		>
			<FileText class="mb-2 h-8 w-8 text-slate-300 dark:text-slate-600" />
			<p class="text-sm text-slate-500 dark:text-slate-400">Aucun document pour ce bien.</p>
			{#if isGerant}
				<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
					Cliquez sur "Ajouter" pour uploader un document.
				</p>
			{/if}
		</div>
	{:else}
		<div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
			{#each documents as doc (doc.id)}
				<div
					class="flex flex-col justify-between rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
				>
					<div>
						<div class="mb-2 flex items-start justify-between gap-2">
							<p class="text-sm font-medium text-slate-900 dark:text-slate-100">
								{doc.nom}
							</p>
							<span
								class="shrink-0 rounded-full px-2 py-0.5 text-[0.65rem] font-semibold {getCategorieBadge(doc.categorie)}"
							>
								{getCategorieLabel(doc.categorie)}
							</span>
						</div>
						<p class="text-xs text-slate-500 dark:text-slate-400">
							{formatFrDate(doc.created_at)}
						</p>
					</div>
					<div class="mt-3 flex items-center gap-2">
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
								onclick={() => handleDelete(doc.id)}
								class="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700 transition-colors hover:bg-rose-100 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-400"
								title="Supprimer"
							>
								<Trash2 class="h-3 w-3" />
								Supprimer
							</button>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
