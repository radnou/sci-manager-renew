<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createFraisForBien, type FraisCreate, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, onSuccess }: Props = $props();

  let loading = $state(false);
  let type_frais = $state('gestion_locative');
  let montant = $state(0);
  let date_frais = $state(new Date().toISOString().slice(0, 10));
  let description = $state('');

  $effect(() => {
    if (open) {
      type_frais = 'gestion_locative'; montant = 0;
      date_frais = new Date().toISOString().slice(0, 10); description = '';
    }
  });

  const fraisTypes = [
    { value: 'gestion_locative', label: 'Gestion locative' },
    { value: 'mise_en_location', label: 'Mise en location' },
    { value: 'autre', label: 'Autre' }
  ];

  async function handleSubmit() {
    if (montant < 0) return;
    loading = true;
    try {
      const data: FraisCreate = { type_frais, montant, date_frais, description: description || undefined };
      await createFraisForBien(sciId, bienId, data);
      addToast({ title: 'Frais ajout\u00e9s', variant: 'success' });
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Ajouter des frais d'agence" submitLabel="Ajouter" {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Type</label>
    <select bind:value={type_frais} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
      {#each fraisTypes as ft}
        <option value={ft.value}>{ft.label}</option>
      {/each}
    </select>
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Montant (&euro;)</label>
    <input type="number" bind:value={montant} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date</label>
    <input type="date" bind:value={date_frais} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Description</label>
    <input type="text" bind:value={description} placeholder="Optionnel"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
