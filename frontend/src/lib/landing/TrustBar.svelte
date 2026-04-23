<script lang="ts">
	import { Shield, Lock, Euro, Server } from 'lucide-svelte';

	const badges = [
		{ icon: Server, text: 'Hébergé en France' },
		{ icon: Lock, text: 'Conforme RGPD' },
		{ icon: Shield, text: 'Satisfait ou remboursé 30j' },
		{ icon: Euro, text: 'Sans engagement' }
	];
</script>

<div class="mt-10 flex flex-wrap items-center justify-center gap-4 text-sm text-slate-500 dark:text-slate-400">
	{#each badges as badge}
		<div class="flex items-center gap-1">
			<badge.icon class="h-4 w-4" />
			<span>{badge.text}</span>
		</div>
		{#if badge !== badges[badges.length - 1]}
			<span class="text-slate-300 dark:text-slate-600">·</span>
		{/if}
	{/each}
</div>
