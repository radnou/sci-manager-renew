<script lang="ts">
	import { Button } from '$lib/components/ui/button';

	interface Action {
		label: string;
		href?: string;
		onclick?: () => void;
		variant?: 'default' | 'outline';
	}

	interface Props {
		icon?: any;
		eyebrow?: string;
		title: string;
		description?: string;
		actions?: Action[];
		align?: 'center' | 'left';
	}

	let {
		icon: Icon,
		eyebrow,
		title,
		description,
		actions = [],
		align = 'center'
	}: Props = $props();
</script>

<div class="rounded-2xl border border-dashed border-border bg-muted/50 px-6 py-10 {align === 'center' ? 'text-center' : 'text-left'}">
	{#if eyebrow}
		<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-muted-foreground">{eyebrow}</p>
	{/if}
	{#if Icon}
		<div class="mb-4 {align === 'center' ? 'mx-auto' : ''} flex h-12 w-12 items-center justify-center rounded-full bg-muted">
			<Icon class="h-6 w-6 text-muted-foreground" />
		</div>
	{/if}
	<h3 class="text-sm font-semibold text-foreground {eyebrow ? 'mt-3 text-lg' : ''}">{title}</h3>
	{#if description}
		<p class="mt-1.5 max-w-sm text-sm text-muted-foreground {align === 'center' ? 'mx-auto' : ''}">{description}</p>
	{/if}
	{#if actions.length > 0}
		<div class="mt-5 flex flex-wrap gap-3 {align === 'center' ? 'justify-center' : ''}">
			{#each actions as action}
				{#if action.href}
					<Button href={action.href} variant={action.variant ?? 'default'} size="sm">{action.label}</Button>
				{:else if action.onclick}
					<Button onclick={action.onclick} variant={action.variant ?? 'default'} size="sm">{action.label}</Button>
				{/if}
			{/each}
		</div>
	{/if}
</div>
