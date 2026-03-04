<script lang="ts">
	import { cn } from '$lib/utils';
	import { dismissToast, toasts, type ToastItem } from './toast-store';

	function cardClass(toast: ToastItem) {
		if (toast.variant === 'success') {
			return 'border-emerald-200 bg-emerald-50 text-emerald-900';
		}
		if (toast.variant === 'error') {
			return 'border-rose-200 bg-rose-50 text-rose-900';
		}
		return 'border-slate-200 bg-white text-slate-900';
	}
</script>

<div class="pointer-events-none fixed right-4 bottom-4 z-50 flex w-[min(92vw,22rem)] flex-col gap-2">
	{#each $toasts as toast (toast.id)}
		<div class={cn('pointer-events-auto rounded-xl border p-3 shadow-xl backdrop-blur-md', cardClass(toast))}>
			<div class="flex items-start justify-between gap-3">
				<div class="space-y-1">
					<p class="text-sm font-semibold">{toast.title}</p>
					{#if toast.description}
						<p class="text-xs opacity-90">{toast.description}</p>
					{/if}
				</div>
				<button
					type="button"
					class="rounded-md px-2 py-1 text-xs font-semibold opacity-70 transition hover:opacity-100"
					onclick={() => dismissToast(toast.id)}
				>
					Fermer
				</button>
			</div>
		</div>
	{/each}
</div>
