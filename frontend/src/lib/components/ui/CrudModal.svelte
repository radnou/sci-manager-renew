<script lang="ts">
  import { scale, fade } from 'svelte/transition';

  interface Props {
    open: boolean;
    title: string;
    subtitle?: string;
    size?: 'compact' | 'wide';
    submitLabel: string;
    loading: boolean;
    onclose?: () => void;
    onsubmit?: () => void;
    children?: import('svelte').Snippet;
  }

  let {
    open = $bindable(),
    title,
    subtitle,
    size = 'compact',
    submitLabel,
    loading,
    onclose,
    onsubmit,
    children
  }: Props = $props();

  const modalId = `modal-${Math.random().toString(36).slice(2, 9)}`;
  let dialogEl: HTMLDivElement | undefined = $state();

  function trapFocus(e: KeyboardEvent) {
    if (e.key !== 'Tab' || !dialogEl) return;
    const focusable = dialogEl.querySelectorAll<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex=\"-1\"])'
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  $effect(() => {
    if (open && dialogEl) {
      requestAnimationFrame(() => {
        const firstInput = dialogEl?.querySelector<HTMLElement>('input:not([disabled]), select:not([disabled]), textarea:not([disabled])');
        if (firstInput) firstInput.focus();
        else dialogEl?.focus();
      });
    }
  });

  function close() {
    if (loading) return;
    open = false;
    onclose?.();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') close();
    trapFocus(e);
  }

  function handleSubmit(e: Event) {
    e.preventDefault();
    onsubmit?.();
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) close();
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    bind:this={dialogEl}
    role="dialog"
    aria-modal="true"
    aria-labelledby="{modalId}-title"
    tabindex="-1"
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    onkeydown={handleKeydown}
  >
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="absolute inset-0 bg-black/50 backdrop-blur-sm"
      transition:fade={{ duration: 150 }}
      onclick={handleBackdropClick}
    ></div>

    <form
      class="relative w-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900 {size === 'wide' ? 'max-w-[560px]' : 'max-w-[420px]'}"
      transition:scale={{ start: 0.95, duration: 150 }}
      onsubmit={handleSubmit}
    >
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
        <div>
          <h2 id="{modalId}-title" class="text-base font-semibold text-slate-900 dark:text-slate-100">
            {title}
          </h2>
          {#if subtitle}
            <p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
          {/if}
        </div>
        <button
          type="button"
          onclick={close}
          class="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
          aria-label="Fermer"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="px-5 py-4 {size === 'wide' ? 'grid grid-cols-2 gap-4' : 'space-y-4'}">
        {#if children}
          {@render children()}
        {/if}
      </div>

      <div class="flex items-center justify-end gap-2 border-t border-slate-200 px-5 py-3 dark:border-slate-700">
        <button
          type="button"
          onclick={close}
          disabled={loading}
          class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
        >
          Annuler
        </button>
        <button
          type="submit"
          disabled={loading}
          class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          {#if loading}
            <span class="inline-flex items-center gap-2">
              <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              Chargement...
            </span>
          {:else}
            {submitLabel}
          {/if}
        </button>
      </div>
    </form>
  </div>
{/if}
