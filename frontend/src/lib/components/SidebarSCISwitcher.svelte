<script lang="ts">
	import { Building2, ChevronDown } from 'lucide-svelte';

	interface Props {
		scis: Array<{ id: string | number; nom: string; statut?: string | null }>;
		activeSciId: string;
		collapsed?: boolean;
		onSciChange?: (id: string) => void;
	}

	let { scis, activeSciId, collapsed = false, onSciChange }: Props = $props();
	let open = $state(false);

	const activeSci = $derived(scis.find((s) => String(s.id) === activeSciId));

	function select(id: string) {
		onSciChange?.(id);
		open = false;
	}
</script>

{#if collapsed}
	<button
		type="button"
		class="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-accent text-sidebar-accent-foreground"
		title={activeSci?.nom ?? 'SCI'}
		onclick={() => (open = !open)}
	>
		<Building2 class="h-4 w-4" />
	</button>
{:else}
	<div class="relative">
		<button
			type="button"
			class="flex w-full items-center gap-2 rounded-lg border border-sidebar-border bg-sidebar px-2.5 py-2 text-left text-sm transition-colors hover:bg-sidebar-accent"
			onclick={() => (open = !open)}
			aria-expanded={open}
		>
			<Building2 class="h-4 w-4 flex-shrink-0 text-sidebar-foreground/60" />
			<span class="flex-1 truncate text-sm font-medium">
				{activeSci?.nom ?? 'Sélectionner une SCI'}
			</span>
			<ChevronDown class="h-3.5 w-3.5 text-sidebar-foreground/50 transition-transform {open ? 'rotate-180' : ''}" />
		</button>

		{#if open}
			<div
				class="absolute left-0 top-full z-50 mt-1 w-full rounded-lg border border-sidebar-border bg-sidebar shadow-lg"
				role="listbox"
			>
				{#each scis as sci (String(sci.id))}
					<button
						type="button"
						role="option"
						aria-selected={String(sci.id) === activeSciId}
						class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors hover:bg-sidebar-accent {String(sci.id) === activeSciId ? 'bg-sidebar-accent font-medium' : ''}"
						onclick={() => select(String(sci.id))}
					>
						<span class="flex-1 truncate">{sci.nom}</span>
						{#if sci.statut}
							<span class="text-[10px] text-sidebar-foreground/50">{sci.statut}</span>
						{/if}
					</button>
				{/each}
			</div>
		{/if}
	</div>
{/if}
