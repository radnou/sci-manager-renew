<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Lock, Check, X } from 'lucide-svelte';
	import { trackEvent, EVENTS } from '$lib/analytics';

	let { open, action, onClose }: { open: boolean; action: string; onClose: () => void } = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onClose();
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		onkeydown={handleKeydown}
		onclick={(e) => { if (e.target === e.currentTarget) onClose(); }}
		role="dialog"
		aria-modal="true"
		aria-labelledby="upgrade-title"
		tabindex="-1"
	>
		<div class="relative mx-4 w-full max-w-md animate-scaleIn rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-900">
			<button
				onclick={onClose}
				class="absolute right-4 top-4 text-gray-400 transition-colors hover:text-gray-600 dark:hover:text-gray-300"
				aria-label="Fermer"
			>
				<X class="h-5 w-5" />
			</button>

			<div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/50">
				<Lock class="h-6 w-6 text-amber-600 dark:text-amber-400" />
			</div>

			<h2 id="upgrade-title" class="mb-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
				Fonctionnalité réservée aux abonnés
			</h2>
			<p class="mb-5 text-sm text-gray-600 dark:text-gray-400">
				Pour {action}, souscrivez un plan GérerSCI.
			</p>

			<ul class="mb-6 space-y-2.5">
				{#each [
					'Accès complet à toutes les fonctionnalités',
					'Vos données réelles, pas de la démo',
					'Support email dédié',
					'Garantie satisfait ou remboursé 30 jours'
				] as item}
					<li class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
						<Check class="h-4 w-4 flex-shrink-0 text-green-500" />
						{item}
					</li>
				{/each}
			</ul>

			<div class="flex items-center gap-3">
				<Button variant="outline" onclick={onClose} class="flex-1">Plus tard</Button>
				<Button href="/pricing" onclick={() => trackEvent(EVENTS.DEMO_UPGRADE_PROMPT, { action })} class="flex-1">Voir les plans →</Button>
			</div>
		</div>
	</div>
{/if}

<style>
	@keyframes scaleIn {
		from {
			opacity: 0;
			transform: scale(0.95);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}

	:global(.animate-scaleIn) {
		animation: scaleIn 0.2s ease-out;
	}
</style>
