<script lang="ts">
	import type { Snippet } from 'svelte';
	import { X } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { cn } from '$lib/utils';

	let {
		open = $bindable(false),
		title = '',
		description = '',
		size = 'lg',
		children,
		footer
	}: {
		open?: boolean;
		title?: string;
		description?: string;
		size?: 'md' | 'lg' | 'xl';
		children?: Snippet;
		footer?: Snippet;
	} = $props();

	const widthClasses = {
		md: 'sm:w-[34rem]',
		lg: 'sm:w-[42rem]',
		xl: 'sm:w-[56rem]'
	};
</script>

<Dialog.Dialog bind:open>
	<Dialog.DialogContent
		showCloseButton={false}
		class={cn(
			'top-0 right-0 left-auto h-dvh max-h-dvh w-full translate-x-0 translate-y-0 gap-0 rounded-none border-0 border-l border-slate-800/90 bg-slate-950/98 p-0 text-slate-50 shadow-[0_0_0_1px_rgba(15,23,42,0.04),-24px_0_60px_-30px_rgba(2,6,23,0.8)] data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-none',
			widthClasses[size]
		)}
	>
		<div class="flex h-full flex-col">
			<div class="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/96 px-6 py-5 backdrop-blur">
				<div class="flex items-start justify-between gap-4">
					<div class="min-w-0">
						<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">
							Action contextuelle
						</p>
						<h2 class="mt-2 text-2xl font-semibold text-slate-50">{title}</h2>
						{#if description}
							<p class="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">{description}</p>
						{/if}
					</div>
					<Button variant="outline" size="icon" class="border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800" onclick={() => (open = false)} aria-label="Fermer le panneau">
						<X class="h-4 w-4" />
					</Button>
				</div>
			</div>

			<div class="flex-1 overflow-y-auto px-6 py-6">
				{@render children?.()}
			</div>

			{#if footer}
				<div class="sticky bottom-0 border-t border-slate-800 bg-slate-950/96 px-6 py-4 backdrop-blur">
					{@render footer?.()}
				</div>
			{/if}
		</div>
	</Dialog.DialogContent>
</Dialog.Dialog>
