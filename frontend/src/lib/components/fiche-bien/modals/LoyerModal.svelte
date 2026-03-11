<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createLoyerForBien, type LoyerCreatePayload, type EntityId, type LoyerStatus } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    defaultMontant?: number;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, defaultMontant = 0, onSuccess }: Props = $props();

  let loading = $state(false);
  let periode = $state(new Date().toISOString().slice(0, 7));
  let montant = $state(defaultMontant);
  let statut = $state<LoyerStatus>('en_attente');

  $effect(() => {
    if (open) {
      montant = defaultMontant;
      statut = 'en_attente';
      periode = new Date().toISOString().slice(0, 7);
    }
  });

  async function handleSubmit() {
    if (!periode || montant < 0) return;
    loading = true;
    try {
      const data: LoyerCreatePayload = {
        id_bien: bienId,
        date_loyer: `${periode}-01`,
        montant,
        statut
      };
      await createLoyerForBien(sciId, bienId, data);
      addToast({ title: 'Loyer enregistré', variant: 'success' });
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Enregistrer un loyer" submitLabel="Enregistrer" {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Période</label>
    <input type="month" bind:value={periode} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Montant (€)</label>
    <input type="number" bind:value={montant} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Statut</label>
    <div class="flex gap-2">
      {#each (['en_attente', 'paye', 'en_retard'] as const) as s}
        <button type="button"
          class="rounded-full px-3 py-1 text-xs font-medium transition-colors {statut === s ? 'bg-sky-600 text-white' : 'border border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-400'}"
          onclick={() => statut = s}>
          {s === 'paye' ? 'Payé' : s === 'en_attente' ? 'En attente' : 'En retard'}
        </button>
      {/each}
    </div>
  </div>
</CrudModal>
