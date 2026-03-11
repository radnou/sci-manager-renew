<script lang="ts">
  import { fade } from 'svelte/transition';

  interface Props {
    open: boolean;
    defaultDate?: string;
    onconfirm: (date: string) => void;
    oncancel?: () => void;
  }

  let { open = $bindable(), defaultDate, onconfirm, oncancel }: Props = $props();

  let dateValue = $state(defaultDate ?? new Date().toISOString().slice(0, 10));

  $effect(() => {
    if (open) {
      dateValue = defaultDate ?? new Date().toISOString().slice(0, 10);
    }
  });

  function confirm() {
    onconfirm(dateValue);
    open = false;
  }

  function cancel() {
    open = false;
    oncancel?.();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') cancel();
    if (e.key === 'Enter') { e.preventDefault(); confirm(); }
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="absolute top-full right-0 z-40 mt-1 rounded-xl border border-slate-200 bg-white p-3 shadow-lg dark:border-slate-700 dark:bg-slate-900"
    transition:fade={{ duration: 100 }}
    onkeydown={handleKeydown}
  >
    <label class="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
      Date de paiement
    </label>
    <input
      type="date"
      bind:value={dateValue}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
    />
    <div class="mt-2 flex justify-end gap-2">
      <button
        type="button"
        onclick={cancel}
        class="rounded-md px-3 py-1 text-xs font-medium text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
      >
        Annuler
      </button>
      <button
        type="button"
        onclick={confirm}
        class="rounded-md bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700"
      >
        Confirmer
      </button>
    </div>
  </div>
{/if}
