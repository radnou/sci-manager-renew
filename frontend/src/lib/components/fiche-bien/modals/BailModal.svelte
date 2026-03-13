<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createBail, updateBail, type BailCreate, type BailUpdate, type BailEmbed, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    editItem?: BailEmbed | null;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, editItem = null, onSuccess }: Props = $props();

  let loading = $state(false);
  let date_debut = $state('');
  let date_fin = $state('');
  let loyer_hc = $state(0);
  let charges_locatives = $state(0);
  let depot_garantie = $state(0);
  let revision_indice = $state('');

  const isEdit = $derived(!!editItem);

  $effect(() => {
    if (open && editItem) {
      date_debut = editItem.date_debut ?? '';
      date_fin = editItem.date_fin ?? '';
      loyer_hc = editItem.loyer_hc ?? 0;
      charges_locatives = editItem.charges_locatives ?? 0;
      depot_garantie = editItem.depot_garantie ?? 0;
      revision_indice = editItem.revision_indice ?? '';
    } else if (open) {
      date_debut = ''; date_fin = ''; loyer_hc = 0;
      charges_locatives = 0; depot_garantie = 0; revision_indice = '';
    }
  });

  async function handleSubmit() {
    if (!date_debut || loyer_hc < 0) return;
    loading = true;
    try {
      if (isEdit && editItem) {
        const data: BailUpdate = { date_fin: date_fin || undefined, loyer_hc, charges_locatives, depot_garantie, revision_indice: revision_indice || undefined };
        await updateBail(sciId, bienId, editItem.id, data);
        addToast({ title: 'Bail mis à jour', variant: 'success' });
      } else {
        const data: BailCreate = { date_debut, date_fin: date_fin || undefined, loyer_hc, charges_locatives, depot_garantie, revision_indice: revision_indice || undefined };
        await createBail(sciId, bienId, data);
        addToast({ title: 'Bail créé', variant: 'success' });
      }
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title={isEdit ? 'Modifier le bail' : 'Créer un bail'} size="wide" submitLabel={isEdit ? 'Mettre à jour' : 'Créer le bail'} {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date début</label>
    <input type="date" bind:value={date_debut} required disabled={isEdit}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 disabled:opacity-50" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date fin</label>
    <input type="date" bind:value={date_fin}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Loyer HC (€)</label>
    <input type="number" bind:value={loyer_hc} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Charges locatives (€)</label>
    <input type="number" bind:value={charges_locatives} min="0" step="0.01"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Dépôt garantie (€)</label>
    <input type="number" bind:value={depot_garantie} min="0" step="0.01"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Indice de révision</label>
    <input type="text" bind:value={revision_indice} placeholder="IRL, ICC..."
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
