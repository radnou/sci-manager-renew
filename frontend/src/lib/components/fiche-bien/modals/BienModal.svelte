<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createBienForSci, type BienCreatePayload, type EntityId, type BienType } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';
  import { goto } from '$app/navigation';

  interface Props {
    open: boolean;
    sciId: EntityId;
  }

  let { open = $bindable(), sciId }: Props = $props();

  let loading = $state(false);
  let adresse = $state('');
  let ville = $state('');
  let code_postal = $state('');
  let type_locatif = $state<BienType>('nu');
  let loyer_cc = $state(0);
  let charges = $state(0);
  let tmi = $state(0);
  let prix_acquisition = $state<number | undefined>(undefined);

  $effect(() => {
    if (open) {
      adresse = ''; ville = ''; code_postal = ''; type_locatif = 'nu';
      loyer_cc = 0; charges = 0; tmi = 0; prix_acquisition = undefined;
    }
  });

  async function handleSubmit() {
    if (!adresse.trim()) return;
    loading = true;
    try {
      const data: BienCreatePayload = {
        id_sci: sciId, adresse: adresse.trim(), ville, code_postal,
        type_locatif, loyer_cc, charges, tmi, prix_acquisition
      };
      const created = await createBienForSci(sciId, data);
      addToast({ title: 'Bien ajouté', variant: 'success' });
      open = false;
      goto(`/scis/${sciId}/biens/${created.id}`);
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Ajouter un bien" size="wide" submitLabel="Ajouter le bien" {loading} onsubmit={handleSubmit}>
  <div class="col-span-2">
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Adresse</label>
    <input type="text" bind:value={adresse} required placeholder="15 rue de la Paix"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Ville</label>
    <input type="text" bind:value={ville} placeholder="Paris"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Code postal</label>
    <input type="text" bind:value={code_postal} placeholder="75001" maxlength="5"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Type</label>
    <select bind:value={type_locatif}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
      <option value="nu">Nu</option>
      <option value="meuble">Meublé</option>
      <option value="mixte">Mixte</option>
    </select>
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Loyer CC (&#8364;)</label>
    <input type="number" bind:value={loyer_cc} min="0" step="0.01"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Prix acquisition (&#8364;)</label>
    <input type="number" bind:value={prix_acquisition} min="0" step="1"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
