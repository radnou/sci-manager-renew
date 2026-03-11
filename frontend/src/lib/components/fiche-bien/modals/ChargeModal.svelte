<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createChargeForBien, type ChargeCreate, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

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

  const chargeTypes = [
    { value: 'copropriete', label: 'Copropriete' },
    { value: 'taxe_fonciere', label: 'Taxe fonciere' },
    { value: 'entretien', label: 'Entretien' },
    { value: 'autre', label: 'Autre' }
  ];

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
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Type de charge</label>
    <select bind:value={type_charge} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
      {#each chargeTypes as ct}
        <option value={ct.value}>{ct.label}</option>
      {/each}
    </select>
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Montant (EUR)</label>
    <input type="number" bind:value={montant} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date</label>
    <input type="date" bind:value={date_paiement} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
