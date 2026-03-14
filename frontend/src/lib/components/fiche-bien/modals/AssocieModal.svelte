<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import {
    inviteAssocie,
    updateAssocie,
    type InviteAssociePayload,
    type AssocieUpdatePayload,
    type Associe,
    type EntityId
  } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    associe?: Associe | null;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, associe = null, onSuccess }: Props = $props();

  let isEdit = $derived(!!associe);

  let loading = $state(false);
  let nom = $state('');
  let email = $state('');
  let role = $state('associe');
  let part = $state(0);

  $effect(() => {
    if (open) {
      if (associe) {
        nom = associe.nom ?? '';
        email = associe.email ?? '';
        role = associe.role ?? 'associe';
        part = associe.part ?? 0;
      } else {
        nom = '';
        email = '';
        role = 'associe';
        part = 0;
      }
    }
  });

  async function handleSubmit() {
    if (!nom.trim() || part <= 0 || part > 100) return;
    loading = true;
    try {
      if (isEdit && associe) {
        const data: AssocieUpdatePayload = { nom: nom.trim(), email: email || null, part, role };
        await updateAssocie(associe.id, data);
        addToast({ title: 'Associé mis à jour', variant: 'success' });
      } else {
        const data: InviteAssociePayload = { nom: nom.trim(), email: email || undefined, part, role };
        const result = await inviteAssocie(sciId, data);
        const emailSent = result?.email_sent;
        addToast({
          title: emailSent
            ? 'Associé ajouté — invitation envoyée par email'
            : 'Associé ajouté',
          variant: 'success'
        });
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

<CrudModal
  bind:open
  title={isEdit ? 'Modifier l\'associé' : 'Inviter un associé'}
  submitLabel={isEdit ? 'Enregistrer' : 'Inviter'}
  {loading}
  onsubmit={handleSubmit}
>
  <div>
    <label for="associe-nom" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Nom</label>
    <input id="associe-nom" type="text" bind:value={nom} required placeholder="Nom complet"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label for="associe-email" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Email</label>
    <input id="associe-email" type="email" bind:value={email} placeholder="optionnel@email.com"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <span id="associe-role-label" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Rôle</span>
    <div class="flex gap-2" role="group" aria-labelledby="associe-role-label">
      {#each (['associe', 'gerant'] as const) as r}
        <button type="button"
          class="rounded-full px-3 py-1 text-xs font-medium transition-colors {role === r ? 'bg-sky-600 text-white' : 'border border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-400'}"
          onclick={() => role = r}>
          {r === 'gerant' ? 'Gérant' : 'Associé'}
        </button>
      {/each}
    </div>
  </div>
  <div>
    <label for="associe-part" class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Part (%)</label>
    <input id="associe-part" type="number" bind:value={part} min="0" max="100" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
