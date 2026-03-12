<script lang="ts">
	import { HandCoins, Building2, FileText, ScrollText, Clock } from 'lucide-svelte';
	import type { ActivityItem } from '$lib/api';

	interface Props {
		activite: ActivityItem[];
	}

	let { activite }: Props = $props();

	const maxItems = 10;
	const displayed = $derived(activite.slice(0, maxItems));

	const typeConfig = {
		loyer: {
			icon: HandCoins,
			color: 'text-emerald-500 dark:text-emerald-400',
			bg: 'bg-emerald-50 dark:bg-emerald-950/40'
		},
		bien: {
			icon: Building2,
			color: 'text-sky-500 dark:text-sky-400',
			bg: 'bg-sky-50 dark:bg-sky-950/40'
		},
		quittance: {
			icon: FileText,
			color: 'text-violet-500 dark:text-violet-400',
			bg: 'bg-violet-50 dark:bg-violet-950/40'
		},
		bail: {
			icon: ScrollText,
			color: 'text-amber-500 dark:text-amber-400',
			bg: 'bg-amber-50 dark:bg-amber-950/40'
		}
	};

	function relativeTime(dateStr: string): string {
		const now = Date.now();
		const then = new Date(dateStr).getTime();
		if (Number.isNaN(then)) return '';

		const diffMs = now - then;
		const diffMinutes = Math.floor(diffMs / 60_000);
		const diffHours = Math.floor(diffMs / 3_600_000);
		const diffDays = Math.floor(diffMs / 86_400_000);

		if (diffMinutes < 1) return "a l'instant";
		if (diffMinutes < 60) return `il y a ${diffMinutes} min`;
		if (diffHours < 24) return `il y a ${diffHours} h`;
		if (diffDays === 1) return 'hier';
		if (diffDays < 30) return `il y a ${diffDays} jours`;
		if (diffDays < 365) {
			const months = Math.floor(diffDays / 30);
			return `il y a ${months} mois`;
		}
		const years = Math.floor(diffDays / 365);
		return `il y a ${years} an${years > 1 ? 's' : ''}`;
	}
</script>

<div class="rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
	<div class="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
		<h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Activite recente</h3>
	</div>

	{#if displayed.length === 0}
		<div class="flex flex-col items-center justify-center px-6 py-10 text-center">
			<div class="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
				<Clock class="h-6 w-6 text-slate-400 dark:text-slate-500" />
			</div>
			<p class="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-100">Aucune activite recente</p>
			<p class="mt-1.5 max-w-xs text-sm text-slate-500 dark:text-slate-400">
				Vos actions apparaitront ici : creation de SCI, ajout de biens, enregistrement de loyers.
			</p>
		</div>
	{:else}
		<div class="divide-y divide-slate-100 dark:divide-slate-800">
			{#each displayed as item (item.id)}
				{@const config = typeConfig[item.type] ?? typeConfig['loyer']}
				<div class="flex items-start gap-3 px-5 py-3.5">
					<div
						class="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg {config.bg}"
					>
						<config.icon class="h-4 w-4 {config.color}" />
					</div>
					<div class="min-w-0 flex-1">
						<p class="text-sm text-slate-700 dark:text-slate-300">{item.description}</p>
						<div class="mt-0.5 flex items-center gap-2 text-xs text-slate-400 dark:text-slate-500">
							<span>{relativeTime(item.created_at)}</span>
							{#if item.sci_nom}
								<span class="text-slate-300 dark:text-slate-600">|</span>
								<span>{item.sci_nom}</span>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
