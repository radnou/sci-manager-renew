<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createPnoForBien, updatePnoForBien, type PnoCreate, type PnoUpdate, type AssurancePnoEmbed, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    editItem?: AssurancePnoEmbed | null;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, editItem = null, onSuccess }: Props = $props();

  let loading = $state(false);
  let assureur = $state('');
  let numero_contrat = $state('');
  let prime_annuelle = $state(0);
  let date_debut = $state('');
  let date_fin = $state('');

  const isEdit = $derived(!!editItem);

  $effect(() => {
    if (open && editItem) {
      assureur = editItem.assureur; numero_contrat = editItem.numero_contrat ?? '';
      prime_annuelle = editItem.prime_annuelle; date_debut = editItem.date_debut;
      date_fin = editItem.date_fin ?? '';
    } else if (open) {
      assureur = ''; numero_contrat = ''; prime_annuelle = 0; date_debut = ''; date_fin = '';
    }
  });

  async function handleSubmit() {
    if (!assureur || !date_debut || prime_annuelle < 0) return;
    loading = true;
    try {
      if (isEdit && editItem) {
        const data: PnoUpdate = { assureur, numero_contrat: numero_contrat || undefined, prime_annuelle, date_debut, date_fin: date_fin || undefined };
        await updatePnoForBien(sciId, bienId, editItem.id, data);
        addToast({ title: 'Assurance PNO mise a jour', variant: 'success' });
      } else {
        const data: PnoCreate = { assureur, numero_contrat: numero_contrat || undefined, prime_annuelle, date_debut, date_fin: date_fin || undefined };
        await createPnoForBien(sciId, bienId, data);
        addToast({ title: 'Assurance PNO ajoutee', variant: 'success' });
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

<CrudModal bind:open title={isEdit ? 'Modifier assurance PNO' : 'Ajouter assurance PNO'} submitLabel={isEdit ? 'Mettre a jour' : 'Ajouter'} {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Assureur</label>
    <input type="text" bind:value={assureur} required placeholder="Nom de l'assureur"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">N contrat</label>
    <input type="text" bind:value={numero_contrat} placeholder="Optionnel"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Prime annuelle (EUR)</label>
    <input type="number" bind:value={prime_annuelle} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date debut</label>
    <input type="date" bind:value={date_debut} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date fin</label>
    <input type="date" bind:value={date_fin}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
