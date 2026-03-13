<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { cn } from '$lib/utils';

	type Trend = 'up' | 'down' | 'neutral';
	type Tone = 'default' | 'success' | 'warning' | 'danger' | 'accent';

	export let label = 'Indicateur';
	export let value: string | number = '-';
	export let caption = '';
	export let trend: Trend = 'neutral';
	export let trendValue = '';
	export let tone: Tone = 'default';
	export let loading = false;

	const toneClasses: Record<Tone, string> = {
		default:
			'border-slate-200/80 from-slate-50/70 to-white dark:border-slate-800 dark:from-slate-900/95 dark:to-slate-950',
		success:
			'border-emerald-200/80 from-emerald-50/80 to-white dark:border-emerald-900/70 dark:from-emerald-950/35 dark:to-slate-950',
		warning:
			'border-amber-200/80 from-amber-50/80 to-white dark:border-amber-900/70 dark:from-amber-950/25 dark:to-slate-950',
		danger:
			'border-rose-200/80 from-rose-50/80 to-white dark:border-rose-900/70 dark:from-rose-950/25 dark:to-slate-950',
		accent:
			'border-cyan-200/80 from-cyan-50/80 to-white dark:border-cyan-900/70 dark:from-cyan-950/25 dark:to-slate-950'
	};

	const trendBadgeClasses: Record<Trend, string> = {
		up: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/55 dark:text-emerald-200',
		down: 'bg-rose-100 text-rose-800 dark:bg-rose-950/55 dark:text-rose-200',
		neutral: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200'
	};

	const trendIcons: Record<Trend, string> = {
		up: '↗',
		down: '↘',
		neutral: '→'
	};
</script>

<Card
	class={cn(
		'relative overflow-hidden border bg-gradient-to-br shadow-[0_14px_40px_-26px_rgba(15,23,42,0.45)]',
		toneClasses[tone]
	)}
	aria-busy={loading}
>
	<div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-cyan-500/70 via-sky-400/80 to-emerald-500/70"></div>
	<CardHeader class="pb-2">
		<CardDescription class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500 dark:text-slate-400">{label}</CardDescription>
		<CardTitle class="text-2xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
			{#if loading}
				<span class="inline-flex h-8 w-28 animate-pulse rounded-md bg-slate-200 dark:bg-slate-800"></span>
			{:else}
				{value}
			{/if}
		</CardTitle>
	</CardHeader>
	<CardContent class="pt-0">
		<div class="flex items-center justify-between gap-3">
			{#if caption}
				<p class="text-xs text-slate-600 dark:text-slate-300">{caption}</p>
			{/if}
			{#if trendValue}
				<span
					class={cn(
						'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase',
						trendBadgeClasses[trend]
					)}
				>
					<span>{trendIcons[trend]}</span>
					{trendValue}
				</span>
			{/if}
		</div>
	</CardContent>
</Card>
