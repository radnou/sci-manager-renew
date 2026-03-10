<script lang="ts">
	import { X, AlertTriangle, CheckCircle, Info } from 'lucide-svelte';

	interface AlertAction {
		label: string;
		onclick: () => void;
		variant?: 'primary' | 'secondary';
	}

	interface Props {
		message: string;
		type?: 'warning' | 'danger' | 'info' | 'success';
		dismissible?: boolean;
		href?: string;
		actions?: AlertAction[];
	}

	let { message, type = 'warning', dismissible = true, href, actions = [] }: Props = $props();
	let dismissed = $state(false);

	const colors = {
		warning:
			'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200',
		danger:
			'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-200',
		info: 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-200',
		success:
			'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200'
	};

	const actionColors = {
		warning: 'bg-amber-700 text-white hover:bg-amber-800 dark:bg-amber-600 dark:hover:bg-amber-500',
		danger: 'bg-rose-700 text-white hover:bg-rose-800 dark:bg-rose-600 dark:hover:bg-rose-500',
		info: 'bg-blue-700 text-white hover:bg-blue-800 dark:bg-blue-600 dark:hover:bg-blue-500',
		success:
			'bg-emerald-700 text-white hover:bg-emerald-800 dark:bg-emerald-600 dark:hover:bg-emerald-500'
	};

	const icons = { warning: AlertTriangle, danger: AlertTriangle, info: Info, success: CheckCircle };
	const Icon = $derived(icons[type]);
</script>

{#if !dismissed}
	<div class="flex items-center gap-3 rounded-xl border px-4 py-3 {colors[type]}">
		<Icon class="h-4 w-4 flex-shrink-0" />
		<p class="flex-1 text-sm font-medium">
			{message}
			{#if href}
				<a {href} class="ml-1 underline underline-offset-2 hover:opacity-80">Voir détails</a>
			{/if}
		</p>
		{#if actions.length > 0}
			<div class="flex items-center gap-2">
				{#each actions as action}
					<button
						type="button"
						class="rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors {action.variant ===
						'secondary'
							? 'opacity-70 hover:opacity-100'
							: actionColors[type]}"
						onclick={action.onclick}
					>
						{action.label}
					</button>
				{/each}
			</div>
		{/if}
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
