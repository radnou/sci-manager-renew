<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createSci, type SCICreatePayload } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';
  import { goto } from '$app/navigation';

  interface Props {
    open: boolean;
  }

  let { open = $bindable() }: Props = $props();

  let loading = $state(false);
  let nom = $state('');
  let siren = $state('');
  let regime_fiscal = $state<'IR' | 'IS'>('IR');

  $effect(() => {
    if (open) { nom = ''; siren = ''; regime_fiscal = 'IR'; }
  });

  async function handleSubmit() {
    if (!nom.trim()) return;
    if (siren && !/^\d{9}$/.test(siren)) {
      addToast({ title: 'SIREN invalide (9 chiffres)', variant: 'error' });
      return;
    }
    loading = true;
    try {
      const data: SCICreatePayload = { nom: nom.trim(), siren: siren || undefined, regime_fiscal };
      const created = await createSci(data);
      addToast({ title: 'SCI créée', variant: 'success' });
      open = false;
      goto(`/scis/${created.id}`);
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Créer une SCI" size="wide" submitLabel="Créer la SCI" {loading} onsubmit={handleSubmit}>
  <div class="col-span-2">
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Nom de la SCI</label>
    <input type="text" bind:value={nom} required placeholder="SCI Mon Patrimoine"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">SIREN (optionnel)</label>
    <input type="text" bind:value={siren} placeholder="123456789" maxlength="9"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Régime fiscal</label>
    <div class="flex gap-2">
      {#each (['IR', 'IS'] as const) as rf}
        <button type="button"
          class="rounded-full px-4 py-1.5 text-xs font-medium transition-colors {regime_fiscal === rf ? 'bg-sky-600 text-white' : 'border border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-400'}"
          onclick={() => regime_fiscal = rf}>
          {rf}
        </button>
      {/each}
    </div>
  </div>
</CrudModal>
