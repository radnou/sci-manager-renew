<script lang="ts">
	import { X, AlertTriangle } from 'lucide-svelte';

	interface Props {
		message: string;
		type?: 'warning' | 'danger' | 'info';
		dismissible?: boolean;
		href?: string;
	}

	let { message, type = 'warning', dismissible = true, href }: Props = $props();
	let dismissed = $state(false);

	const colors = {
		warning: 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200',
		danger: 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-200',
		info: 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-200'
	};
</script>

{#if !dismissed}
	<div class="flex items-center gap-3 rounded-xl border px-4 py-3 {colors[type]}">
		<AlertTriangle class="h-4 w-4 flex-shrink-0" />
		<p class="flex-1 text-sm font-medium">
			{message}
			{#if href}
				<a href={href} class="ml-1 underline underline-offset-2 hover:opacity-80">Voir détails</a>
			{/if}
		</p>
		{#if dismissible}
			<button
				type="button"
				class="rounded-md p-1 opacity-60 hover:opacity-100"
				onclick={() => (dismissed = true)}
				aria-label="Fermer"
			>
				<X class="h-3.5 w-3.5" />
			</button>
		{/if}
	</div>
{/if}
