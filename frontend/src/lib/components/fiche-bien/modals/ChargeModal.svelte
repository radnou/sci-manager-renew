<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createChargeForBien, type ChargeCreate, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';
  import { CHARGE_TYPE_OPTIONS } from '$lib/high-value/charges';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, onSuccess }: Props = $props();

  let loading = $state(false);
  let type_charge = $state('copropriete');
  let montant = $state(0);
  let date_paiement = $state(new Date().toISOString().slice(0, 10));

  $effect(() => {
    if (open) {
      type_charge = 'copropriete'; montant = 0;
      date_paiement = new Date().toISOString().slice(0, 10);
    }
  });

  async function handleSubmit() {
    if (montant < 0) return;
    loading = true;
    try {
      const data: ChargeCreate = { type_charge, montant, date_paiement };
      await createChargeForBien(sciId, bienId, data);
      addToast({ title: 'Charge ajoutee', variant: 'success' });
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Ajouter une charge" submitLabel="Ajouter" {loading} onsubmit={handleSubmit}>
  <div>
    <label for="charge-type" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Type de charge</label>
    <select id="charge-type" bind:value={type_charge} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
      {#each CHARGE_TYPE_OPTIONS as ct}
        <option value={ct.value}>{ct.label}</option>
      {/each}
    </select>
  </div>
  <div>
    <label for="charge-montant" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Montant (EUR)</label>
    <input id="charge-montant" type="number" bind:value={montant} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label for="charge-date" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date</label>
    <input id="charge-date" type="date" bind:value={date_paiement} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
