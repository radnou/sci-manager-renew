<script lang="ts">
	import { Info } from 'lucide-svelte';

	interface Props {
		text: string;
	}

	let { text }: Props = $props();

	let showTooltip = $state(false);
</script>

<span class="relative ml-1 inline-block">
	<button
		type="button"
		aria-label="Plus d'informations"
		class="text-slate-400 transition-colors hover:text-blue-500 dark:text-slate-500 dark:hover:text-blue-400"
		onmouseenter={() => (showTooltip = true)}
		onmouseleave={() => (showTooltip = false)}
		onclick={() => (showTooltip = !showTooltip)}
	>
		<Info class="h-3.5 w-3.5" />
	</button>

	{#if showTooltip}
		<div
			class="absolute bottom-full left-1/2 z-50 mb-2 w-56 -translate-x-1/2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs leading-relaxed text-slate-600 shadow-lg dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"
			role="tooltip"
		>
			{text}
			<!-- Arrow border (behind) -->
			<div
				class="absolute left-1/2 top-full -translate-x-1/2 border-[6px] border-transparent border-t-slate-200 dark:border-t-slate-700"
			></div>
			<!-- Arrow fill (on top) -->
			<div
				class="absolute left-1/2 top-full -mt-px -translate-x-1/2 border-[6px] border-transparent border-t-white dark:border-t-slate-800"
			></div>
		</div>
	{/if}
</span>
