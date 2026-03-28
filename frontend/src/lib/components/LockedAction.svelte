<script lang="ts">
	import type { Snippet } from 'svelte';
	import { Lock } from 'lucide-svelte';
	import UpgradePrompt from './UpgradePrompt.svelte';

	let { isDemo, action, children }: { isDemo: boolean; action: string; children: Snippet } = $props();

	let showPrompt = $state(false);
</script>

{#if !isDemo}
	{@render children()}
{:else}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="relative"
		onclick={(e) => { e.preventDefault(); e.stopPropagation(); showPrompt = true; }}
		onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); showPrompt = true; } }}
	>
		{@render children()}
		<div class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 shadow-sm">
			<Lock class="h-3 w-3 text-white" />
		</div>
	</div>

	<UpgradePrompt open={showPrompt} {action} onClose={() => (showPrompt = false)} />
{/if}
