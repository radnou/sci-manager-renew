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
  let nom_agence = $state('');
  let contact = $state('');
  let type_frais = $state<'pourcentage' | 'fixe'>('pourcentage');
  let montant_ou_pourcentage = $state(0);

  $effect(() => {
    if (open) {
      nom_agence = '';
      contact = '';
      type_frais = 'pourcentage';
      montant_ou_pourcentage = 0;
    }
  });

  const fraisTypes = [
    { value: 'pourcentage', label: 'Pourcentage (%)' },
    { value: 'fixe', label: 'Montant fixe (€)' }
  ];

  async function handleSubmit() {
    if (!nom_agence.trim()) {
      addToast({ title: 'Le nom de l\'agence est requis', variant: 'error' });
      return;
    }
    if (montant_ou_pourcentage < 0) {
      addToast({ title: 'Le montant ou pourcentage doit être positif', variant: 'error' });
      return;
    }
    loading = true;
    try {
      const data: FraisCreate = {
        nom_agence: nom_agence.trim(),
        contact: contact.trim() || undefined,
        type_frais,
        montant_ou_pourcentage
      };
      await createFraisForBien(sciId, bienId, data);
      addToast({ title: 'Frais ajoutés', variant: 'success' });
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
    <label for="frais-nom-agence" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Nom de l'agence</label>
    <input id="frais-nom-agence" type="text" bind:value={nom_agence} required placeholder="ex: Foncia"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label for="frais-type" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Type de frais</label>
    <select id="frais-type" bind:value={type_frais} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
      {#each fraisTypes as ft}
        <option value={ft.value}>{ft.label}</option>
      {/each}
    </select>
  </div>
  <div>
    <label for="frais-valeur" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
      {type_frais === 'pourcentage' ? 'Pourcentage (%)' : 'Montant (€)'}
    </label>
    <input id="frais-valeur" type="number" bind:value={montant_ou_pourcentage} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label for="frais-contact" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Contact (Optionnel)</label>
    <input id="frais-contact" type="text" bind:value={contact} placeholder="ex: email ou téléphone"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
