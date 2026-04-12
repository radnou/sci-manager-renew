<script lang="ts">
	import { Info } from 'lucide-svelte';
	import { computePosition, flip, shift, offset, arrow } from '@floating-ui/dom';

	interface Props {
		text: string;
	}

	let { text }: Props = $props();

	let showTooltip = $state(false);
	let triggerEl = $state<HTMLElement | null>(null);
	let tooltipEl = $state<HTMLElement | null>(null);
	let arrowEl = $state<HTMLElement | null>(null);

	async function updatePosition() {
		if (!triggerEl || !tooltipEl) return;
		const { x, y, placement, middlewareData } = await computePosition(triggerEl, tooltipEl, {
			placement: 'top',
			middleware: [offset(8), flip(), shift({ padding: 8 }), ...(arrowEl ? [arrow({ element: arrowEl })] : [])]
		});
		Object.assign(tooltipEl.style, { left: `${x}px`, top: `${y}px` });
		if (arrowEl && middlewareData.arrow) {
			const { x: ax } = middlewareData.arrow;
			const side = placement.includes('top') ? 'bottom' : 'top';
			Object.assign(arrowEl.style, {
				left: ax != null ? `${ax}px` : '',
				[side]: '-4px'
			});
		}
	}

	function show() {
		showTooltip = true;
		requestAnimationFrame(updatePosition);
	}

	function hide() {
		showTooltip = false;
	}
</script>

<span class="relative ml-1 inline-flex items-center">
	<button
		type="button"
		aria-label="Plus d'informations"
		class="text-slate-400 transition-colors hover:text-blue-500 dark:text-slate-500 dark:hover:text-blue-400"
		bind:this={triggerEl}
		onmouseenter={show}
		onmouseleave={hide}
		onfocus={show}
		onblur={hide}
		onclick={() => (showTooltip ? hide() : show())}
	>
		<Info class="h-3.5 w-3.5" />
	</button>

	{#if showTooltip}
		<div
			bind:this={tooltipEl}
			class="fixed z-[9999] w-60 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs leading-relaxed text-slate-600 shadow-lg dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
			role="tooltip"
		>
			{text}
			<div
				bind:this={arrowEl}
				class="absolute h-2 w-2 rotate-45 border-b border-r border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800"
			></div>
		</div>
	{/if}
</span>
