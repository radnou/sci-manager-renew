<script lang="ts">
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import type { ComponentType } from 'svelte';

	interface Props {
		icon?: ComponentType;
		title: string;
		description: string;
		badge?: string;
		features?: string[];
		class?: string;
	}

	let { icon: Icon, title, description, badge, features = [], class: className = '' }: Props = $props();
</script>

<Card class="group relative overflow-hidden border-slate-200/60 bg-white/80 shadow-lg backdrop-blur-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1 dark:border-slate-700/60 dark:bg-slate-800/80 {className}">
	{#if badge}
		<div class="absolute top-4 right-4">
			<Badge variant="secondary" class="text-xs font-medium">
				{badge}
			</Badge>
		</div>
	{/if}

	<CardHeader class="pb-4">
		{#if Icon}
			<div class="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg">
				<Icon class="h-6 w-6" />
			</div>
		{/if}
		<CardTitle class="text-xl font-semibold text-slate-900 dark:text-slate-100">
			{title}
		</CardTitle>
		<CardDescription class="text-slate-600 dark:text-slate-400">
			{description}
		</CardDescription>
	</CardHeader>

	{#if features.length > 0}
		<CardContent class="pt-0">
			<ul class="space-y-2">
				{#each features as feature}
					<li class="flex items-center text-sm text-slate-700 dark:text-slate-300">
						<div class="mr-3 h-1.5 w-1.5 rounded-full bg-blue-500"></div>
						{feature}
					</li>
				{/each}
			</ul>
		</CardContent>
	{/if}
</Card>
