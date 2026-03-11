<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { inviteAssocie, type InviteAssociePayload, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, onSuccess }: Props = $props();

  let loading = $state(false);
  let nom = $state('');
  let email = $state('');
  let role = $state('associe');
  let part = $state(0);

  $effect(() => {
    if (open) { nom = ''; email = ''; role = 'associe'; part = 0; }
  });

  async function handleSubmit() {
    if (!nom.trim() || part <= 0 || part > 100) return;
    loading = true;
    try {
      const data: InviteAssociePayload = { nom: nom.trim(), email: email || undefined, part, role };
      await inviteAssocie(sciId, data);
      addToast({ title: 'Associ\u00e9 invit\u00e9', variant: 'success' });
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Inviter un associ\u00e9" submitLabel="Inviter" {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Nom</label>
    <input type="text" bind:value={nom} required placeholder="Nom complet"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Email</label>
    <input type="email" bind:value={email} placeholder="optionnel@email.com"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">R\u00f4le</label>
    <div class="flex gap-2">
      {#each (['associe', 'gerant'] as const) as r}
        <button type="button"
          class="rounded-full px-3 py-1 text-xs font-medium transition-colors {role === r ? 'bg-sky-600 text-white' : 'border border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-400'}"
          onclick={() => role = r}>
          {r === 'gerant' ? 'G\u00e9rant' : 'Associ\u00e9'}
        </button>
      {/each}
    </div>
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Part (%)</label>
    <input type="number" bind:value={part} min="0" max="100" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
