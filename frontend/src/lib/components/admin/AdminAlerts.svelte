<script lang="ts">
	import { CircleAlert, TriangleAlert, CircleCheck } from 'lucide-svelte';

	type Alert = {
		type: string;
		severity: 'high' | 'medium' | 'info';
		message: string;
		detail: string;
		tooltip: string;
	};

	type Props = { alerts: Alert[] };
	let { alerts }: Props = $props();

	const severityConfig: Record<
		string,
		{ border: string; bg: string; icon: typeof CircleAlert; iconColor: string }
	> = {
		high: {
			border: 'border-rose-200 dark:border-rose-800',
			bg: 'bg-rose-50 dark:bg-rose-950/30',
			icon: CircleAlert,
			iconColor: 'text-rose-500'
		},
		medium: {
			border: 'border-amber-200 dark:border-amber-800',
			bg: 'bg-amber-50 dark:bg-amber-950/30',
			icon: TriangleAlert,
			iconColor: 'text-amber-500'
		}
	};
</script>

{#if alerts.length === 0}
	<div
		class="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-4 dark:border-emerald-800 dark:bg-emerald-950/30"
	>
		<CircleCheck class="h-5 w-5 flex-shrink-0 text-emerald-500" />
		<p class="text-sm font-medium text-emerald-700 dark:text-emerald-300">
			Tout va bien — aucune alerte business
		</p>
	</div>
{:else}
	<div class="space-y-3">
		{#each alerts as alert (alert.type)}
			{@const config = severityConfig[alert.severity] ?? severityConfig.medium}
			<div class="flex items-start gap-3 rounded-xl border px-5 py-4 {config.border} {config.bg}">
				<config.icon class="mt-0.5 h-5 w-5 flex-shrink-0 {config.iconColor}" />
				<div class="min-w-0 flex-1">
					<p class="text-sm font-medium text-slate-900 dark:text-slate-100">{alert.message}</p>
					<p class="mt-0.5 text-xs text-slate-600 dark:text-slate-400">{alert.detail}</p>
					<p class="mt-1 text-xs text-slate-500 italic dark:text-slate-500">{alert.tooltip}</p>
				</div>
			</div>
		{/each}
	</div>
{/if}
