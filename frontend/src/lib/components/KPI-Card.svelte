<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { cn } from '$lib/utils';

	type Trend = 'up' | 'down' | 'neutral';
	type Tone = 'default' | 'success' | 'warning' | 'danger' | 'accent';

	interface Props {
		label?: string;
		value?: string | number;
		caption?: string;
		trend?: Trend;
		trendValue?: string;
		tone?: Tone;
		loading?: boolean;
	}

	let {
		label = 'Indicateur',
		value = '-',
		caption = '',
		trend = 'neutral',
		trendValue = '',
		tone = 'default',
		loading = false
	}: Props = $props();

	const toneClasses: Record<Tone, string> = {
		default: 'border-border bg-card',
		success: 'border-ds-success/30 bg-ds-success-soft',
		warning: 'border-ds-warning/30 bg-ds-warning-soft',
		danger: 'border-ds-error/30 bg-ds-error-soft',
		accent: 'border-ds-accent/30 bg-ds-accent-soft'
	};

	const trendBadgeClasses: Record<Trend, string> = {
		up: 'bg-ds-success-soft text-ds-success',
		down: 'bg-ds-error-soft text-ds-error',
		neutral: 'bg-secondary text-secondary-foreground'
	};

	const trendIcons: Record<Trend, string> = {
		up: '↗',
		down: '↘',
		neutral: '→'
	};
</script>

<Card
	class={cn(
		'relative overflow-hidden border shadow-sm',
		toneClasses[tone]
	)}
	aria-busy={loading}
>
	<CardHeader class="pb-2">
		<CardDescription class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-muted-foreground">
			{label}
		</CardDescription>
		<CardTitle class="text-2xl font-semibold tracking-tight text-foreground">
			{#if loading}
				<span class="inline-flex h-8 w-28 animate-pulse rounded-md bg-muted"></span>
			{:else}
				{value}
			{/if}
		</CardTitle>
	</CardHeader>
	<CardContent class="pt-0">
		<div class="flex items-center justify-between gap-3">
			{#if caption}
				<p class="text-xs text-muted-foreground">{caption}</p>
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
