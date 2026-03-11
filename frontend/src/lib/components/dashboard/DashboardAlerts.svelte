<script lang="ts">
	import { CircleAlert, TriangleAlert, Info, CircleCheck } from 'lucide-svelte';
	import type { DashboardAlerte } from '$lib/api';

	interface Props {
		alertes: DashboardAlerte[];
	}

	let { alertes }: Props = $props();

	const severityConfig = {
		error: {
			icon: CircleAlert,
			bg: 'bg-rose-50 dark:bg-rose-950/30',
			border: 'border-rose-200 dark:border-rose-800',
			text: 'text-rose-700 dark:text-rose-300',
			iconColor: 'text-rose-500 dark:text-rose-400'
		},
		warning: {
			icon: TriangleAlert,
			bg: 'bg-amber-50 dark:bg-amber-950/30',
			border: 'border-amber-200 dark:border-amber-800',
			text: 'text-amber-700 dark:text-amber-300',
			iconColor: 'text-amber-500 dark:text-amber-400'
		},
		info: {
			icon: Info,
			bg: 'bg-blue-50 dark:bg-blue-950/30',
			border: 'border-blue-200 dark:border-blue-800',
			text: 'text-blue-700 dark:text-blue-300',
			iconColor: 'text-blue-500 dark:text-blue-400'
		}
	};
</script>

{#if alertes.length === 0}
	<div
		class="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-4 dark:border-emerald-800 dark:bg-emerald-950/30"
	>
		<CircleCheck class="h-5 w-5 flex-shrink-0 text-emerald-500 dark:text-emerald-400" />
		<p class="text-sm font-medium text-emerald-700 dark:text-emerald-300">
			Tout est en ordre — aucune alerte en cours.
		</p>
	</div>
{:else}
	<div class="space-y-3">
		{#each alertes as alerte (alerte.message)}
			{@const config = severityConfig[alerte.severity]}
			<div
				class="flex items-start gap-3 rounded-xl border px-5 py-4 {config.bg} {config.border}"
			>
				<config.icon class="mt-0.5 h-5 w-5 flex-shrink-0 {config.iconColor}" />
				<div class="min-w-0 flex-1">
					<p class="text-sm font-medium {config.text}">{alerte.message}</p>
					{#if alerte.sci_nom || alerte.bien_adresse}
						<p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
							{#if alerte.sci_nom}{alerte.sci_nom}{/if}
							{#if alerte.sci_nom && alerte.bien_adresse} — {/if}
							{#if alerte.bien_adresse}{alerte.bien_adresse}{/if}
						</p>
					{/if}
				</div>
				{#if alerte.link}
					<a
						href={alerte.link}
						class="flex-shrink-0 text-xs font-semibold {config.text} underline underline-offset-2 hover:no-underline"
					>
						Voir
					</a>
				{/if}
			</div>
		{/each}
	</div>
{/if}
