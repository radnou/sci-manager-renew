<script lang="ts">
  interface Tab {
    id: string;
    label: string;
    badge?: number;
  }

  interface Props {
    tabs: Tab[];
    activeTab: string;
    onTabChange?: (id: string) => void;
  }

  let { tabs, activeTab, onTabChange }: Props = $props();
</script>

<div class="flex gap-1 overflow-x-auto border-b border-border" role="tablist">
  {#each tabs as tab (tab.id)}
    <button
      type="button"
      role="tab"
      aria-selected={activeTab === tab.id}
      class="relative flex shrink-0 items-center gap-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors
        {activeTab === tab.id
          ? 'text-ds-accent after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-ds-accent'
          : 'text-muted-foreground hover:text-foreground'}"
      onclick={() => onTabChange?.(tab.id)}
    >
      {tab.label}
      {#if tab.badge && tab.badge > 0}
        <span class="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-ds-error px-1.5 text-[11px] font-semibold text-white">
          {tab.badge}
        </span>
      {/if}
    </button>
  {/each}
</div>
