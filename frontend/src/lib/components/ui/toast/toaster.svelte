<script lang="ts">
	import { cn } from '$lib/utils';
	import { dismissToast, handleUndo, toasts, type ToastItem } from './toast-store';

	function cardClass(toast: ToastItem) {
		if (toast.variant === 'success') {
			return 'border-emerald-200 bg-emerald-50 text-emerald-900';
		}
		if (toast.variant === 'error') {
			return 'border-rose-200 bg-rose-50 text-rose-900';
		}
		if (toast.variant === 'undo') {
			return 'border-amber-200 bg-amber-50 text-amber-900';
		}
		return 'border-slate-200 bg-white text-slate-900';
	}
</script>

<div
	aria-live="polite"
	class="pointer-events-none fixed right-4 bottom-4 z-50 flex w-[min(92vw,22rem)] flex-col gap-2"
>
	{#each $toasts as toast (toast.id)}
		<div class={cn('pointer-events-auto rounded-xl border p-3 shadow-xl backdrop-blur-md', cardClass(toast))}>
			<div class="flex items-start justify-between gap-3">
				<div class="space-y-1">
					<p class="text-sm font-semibold">{toast.title}</p>
					{#if toast.description}
						<p class="text-xs opacity-90">{toast.description}</p>
					{/if}
				</div>
				{#if toast.variant === 'undo'}
					<button
						type="button"
						class="rounded-md bg-amber-600 px-3 py-1 text-xs font-semibold text-white transition hover:bg-amber-700"
						onclick={() => handleUndo(toast.id)}
					>
						Annuler
					</button>
				{:else}
					<button
						type="button"
						class="rounded-md px-2 py-1 text-xs font-semibold opacity-70 transition hover:opacity-100"
						onclick={() => dismissToast(toast.id)}
					>
						Fermer
					</button>
				{/if}
			</div>
			{#if toast.variant === 'undo'}
				<div class="mt-2 h-1 w-full overflow-hidden rounded-full bg-amber-200">
					<div
						class="h-full rounded-full bg-amber-500"
						style="animation: shrink {toast.timeoutMs}ms linear forwards"
					></div>
				</div>
			{/if}
		</div>
	{/each}
</div>

<style>
	@keyframes shrink {
		from { width: 100%; }
		to { width: 0%; }
	}
</style>
