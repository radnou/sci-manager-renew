<script lang="ts">
  import { scale, fade } from 'svelte/transition';
  import { Download, Upload, FileText, X, Check, AlertCircle, Loader2 } from 'lucide-svelte';
  import { addToast } from '$lib/components/ui/toast/toast-store';
  import { downloadImportTemplate, importCsv, type ImportResult, type EntityId } from '$lib/api';

  interface Props {
    open: boolean;
    sciId: EntityId;
    onClose: () => void;
    onSuccess: () => void;
  }

  let { open, sciId, onClose, onSuccess }: Props = $props();

  let activeTab = $state<'biens' | 'loyers'>('biens');
  let file: File | null = $state(null);
  let importing = $state(false);
  let result: ImportResult | null = $state(null);
  let dragOver = $state(false);

  const modalId = `modal-import-${Math.random().toString(36).slice(2, 9)}`;

  function resetState() {
    file = null;
    importing = false;
    result = null;
    dragOver = false;
  }

  $effect(() => {
    if (open) {
      resetState();
    }
  });

  function close() {
    if (importing) return;
    resetState();
    onClose();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') close();
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) close();
  }

  function switchTab(tab: 'biens' | 'loyers') {
    activeTab = tab;
    file = null;
    result = null;
  }

  async function handleDownloadTemplate() {
    try {
      const blob = await downloadImportTemplate(activeTab);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `template-${activeTab}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      addToast({
        title: 'Erreur',
        description: err?.message ?? 'Impossible de telecharger le template.',
        variant: 'error'
      });
    }
  }

  function handleFileInput(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      file = input.files[0];
      result = null;
    }
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    dragOver = false;
    if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
      const dropped = e.dataTransfer.files[0];
      if (dropped.name.endsWith('.csv') || dropped.type === 'text/csv') {
        file = dropped;
        result = null;
      } else {
        addToast({
          title: 'Format invalide',
          description: 'Veuillez selectionner un fichier CSV.',
          variant: 'error'
        });
      }
    }
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    dragOver = true;
  }

  function handleDragLeave() {
    dragOver = false;
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  }

  async function handleImport() {
    if (!file) return;
    importing = true;
    result = null;
    try {
      result = await importCsv(sciId, activeTab, file);
      if (result.success && result.imported > 0) {
        addToast({
          title: 'Import termine',
          description: `${result.imported} ${activeTab === 'biens' ? 'bien(s)' : 'loyer(s)'} importe(s).`,
          variant: 'success'
        });
        onSuccess();
      }
    } catch (err: any) {
      addToast({
        title: 'Erreur d\'import',
        description: err?.message ?? 'Erreur lors de l\'import.',
        variant: 'error'
      });
    } finally {
      importing = false;
    }
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    role="dialog"
    aria-modal="true"
    aria-labelledby="{modalId}-title"
    tabindex="-1"
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    onkeydown={handleKeydown}
  >
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="absolute inset-0 bg-black/50 backdrop-blur-sm"
      transition:fade={{ duration: 150 }}
      onclick={handleBackdropClick}
    ></div>

    <div
      class="relative w-full max-w-[520px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900"
      transition:scale={{ start: 0.95, duration: 150 }}
    >
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
        <div>
          <h2 id="{modalId}-title" class="text-base font-semibold text-slate-900 dark:text-slate-100">
            Importer depuis un CSV
          </h2>
          <p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Importez vos biens ou loyers en masse
          </p>
        </div>
        <button
          type="button"
          onclick={close}
          class="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
          aria-label="Fermer"
        >
          <X class="h-5 w-5" />
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-slate-200 dark:border-slate-700">
        <button
          type="button"
          onclick={() => switchTab('biens')}
          class="flex-1 px-4 py-2.5 text-sm font-medium transition-colors {activeTab === 'biens' ? 'border-b-2 border-sky-600 text-sky-600 dark:text-sky-400 dark:border-sky-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}"
        >
          Biens
        </button>
        <button
          type="button"
          onclick={() => switchTab('loyers')}
          class="flex-1 px-4 py-2.5 text-sm font-medium transition-colors {activeTab === 'loyers' ? 'border-b-2 border-sky-600 text-sky-600 dark:text-sky-400 dark:border-sky-400' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}"
        >
          Loyers
        </button>
      </div>

      <!-- Body -->
      <div class="px-5 py-4 space-y-4">
        <!-- Template download -->
        <button
          type="button"
          onclick={handleDownloadTemplate}
          class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          <Download class="h-4 w-4 text-sky-600 dark:text-sky-400" />
          Telecharger le template {activeTab === 'biens' ? 'biens' : 'loyers'}
        </button>

        <!-- Drop zone -->
        <div
          role="button"
          tabindex="0"
          ondrop={handleDrop}
          ondragover={handleDragOver}
          ondragleave={handleDragLeave}
          onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') document.getElementById(`${modalId}-file-input`)?.click(); }}
          onclick={() => document.getElementById(`${modalId}-file-input`)?.click()}
          class="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-8 transition-colors {dragOver ? 'border-sky-500 bg-sky-50 dark:border-sky-400 dark:bg-sky-950/30' : 'border-slate-300 hover:border-slate-400 dark:border-slate-600 dark:hover:border-slate-500'}"
        >
          <Upload class="mb-2 h-8 w-8 text-slate-400 dark:text-slate-500" />
          <p class="text-sm font-medium text-slate-600 dark:text-slate-400">
            Glissez votre fichier CSV ici
          </p>
          <p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
            ou cliquez pour parcourir
          </p>
          <input
            id="{modalId}-file-input"
            type="file"
            accept=".csv,text/csv"
            class="hidden"
            onchange={handleFileInput}
          />
        </div>

        <!-- Selected file preview -->
        {#if file}
          <div class="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800">
            <FileText class="h-5 w-5 shrink-0 text-sky-600 dark:text-sky-400" />
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-slate-800 dark:text-slate-200">{file.name}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">{formatFileSize(file.size)}</p>
            </div>
            <button
              type="button"
              onclick={() => { file = null; result = null; }}
              class="rounded p-1 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-300"
              aria-label="Retirer le fichier"
            >
              <X class="h-4 w-4" />
            </button>
          </div>
        {/if}

        <!-- Result display -->
        {#if result}
          <div class="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/50">
            {#if result.imported > 0}
              <div class="flex items-center gap-2 text-sm text-emerald-700 dark:text-emerald-400">
                <Check class="h-4 w-4 shrink-0" />
                <span>{result.imported} {activeTab === 'biens' ? 'bien(s)' : 'loyer(s)'} importe(s)</span>
              </div>
            {/if}
            {#if result.skipped > 0}
              <div class="flex items-center gap-2 text-sm text-amber-700 dark:text-amber-400">
                <AlertCircle class="h-4 w-4 shrink-0" />
                <span>{result.skipped} ligne(s) ignoree(s)</span>
              </div>
            {/if}
            {#if result.errors.length > 0}
              <div class="space-y-1">
                <div class="flex items-center gap-2 text-sm font-medium text-rose-700 dark:text-rose-400">
                  <AlertCircle class="h-4 w-4 shrink-0" />
                  <span>{result.errors.length} erreur(s)</span>
                </div>
                <ul class="ml-6 list-disc space-y-0.5 text-xs text-rose-600 dark:text-rose-400">
                  {#each result.errors.slice(0, 5) as err}
                    <li>{err}</li>
                  {/each}
                  {#if result.errors.length > 5}
                    <li class="text-slate-500 dark:text-slate-400">
                      ... et {result.errors.length - 5} autre(s)
                    </li>
                  {/if}
                </ul>
              </div>
            {/if}
          </div>
        {/if}
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-2 border-t border-slate-200 px-5 py-3 dark:border-slate-700">
        <button
          type="button"
          onclick={close}
          disabled={importing}
          class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
        >
          Fermer
        </button>
        <button
          type="button"
          onclick={handleImport}
          disabled={!file || importing}
          class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
        >
          {#if importing}
            <Loader2 class="h-4 w-4 animate-spin" />
            Import en cours...
          {:else}
            <Upload class="h-4 w-4" />
            Importer
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}
