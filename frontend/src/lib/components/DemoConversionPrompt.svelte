<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { X } from 'lucide-svelte';
	import { trackEvent, EVENTS } from '$lib/analytics';

	interface Props {
		message: string;
		open: boolean;
		onClose: () => void;
	}

	let { message, open, onClose }: Props = $props();

	function handleConvert() {
		trackEvent(EVENTS.DEMO_UPGRADE_PROMPT, { action: 'convert_from_prompt' });
		window.location.href = '/pricing';
	}

	function handleContinue() {
		localStorage.setItem('demo_prompt_dismissed', String(Date.now()));
		onClose();
	}
</script>

{#if open}
	<div
		class="fixed bottom-6 left-1/2 z-40 w-full max-w-lg -translate-x-1/2 px-4"
		style="animation: slideUp 0.3s ease-out"
	>
		<div class="rounded-2xl border border-blue-200 bg-white p-5 shadow-2xl dark:border-blue-800 dark:bg-slate-900">
			<button
				class="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
				onclick={handleContinue}
				aria-label="Fermer"
			>
				<X class="h-4 w-4" />
			</button>

			<p class="pr-6 text-sm font-medium text-slate-700 dark:text-slate-300">
				{message}
			</p>
			<p class="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
				Ajoutez votre première SCI pour gérer vos vraies données.
			</p>

			<div class="mt-4 flex items-center gap-3">
				<Button
					class="bg-blue-600 text-white hover:bg-blue-700"
					size="sm"
					onclick={handleConvert}
				>
					Commencer avec mes vraies données →
				</Button>
				<button
					class="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
					onclick={handleContinue}
				>
					Continuer l'exploration
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	@keyframes slideUp {
		from {
			opacity: 0;
			transform: translate(-50%, 20px);
		}
		to {
			opacity: 1;
			transform: translate(-50%, 0);
		}
	}
</style>
