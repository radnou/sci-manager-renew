<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { ArrowRight, TrendingUp, Users, Shield } from 'lucide-svelte';

	interface Props {
		title: string;
		subtitle: string;
		description: string;
		primaryCta: {
			text: string;
			href: string;
		};
		secondaryCta: {
			text: string;
			href: string;
		};
		kpis?: Array<{
			value: string;
			label: string;
		}>;
		badges?: string[];
	}

	let {
		title,
		subtitle,
		description,
		primaryCta,
		secondaryCta,
		kpis = [],
		badges = []
	}: Props = $props();
</script>

<section class="relative overflow-hidden bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
	<!-- Background decoration -->
	<div class="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-slate-700/25 dark:[mask-image:linear-gradient(0deg,rgba(255,255,255,0.1),rgba(255,255,255,0.5))]"></div>
	<div class="absolute inset-0 bg-gradient-to-r from-slate-900/5 via-transparent to-slate-900/5 dark:from-slate-100/5 dark:to-slate-100/5"></div>

	<div class="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
		<div class="mx-auto max-w-2xl text-center">
			{#if badges.length > 0}
				<div class="mb-8 flex flex-wrap items-center justify-center gap-2">
					{#each badges as badge}
						<Badge variant="secondary" class="px-3 py-1 text-xs font-medium">
							{badge}
						</Badge>
					{/each}
				</div>
			{/if}

			<h1 class="text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-6xl">
				{title}
				<span class="block bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
					{subtitle}
				</span>
			</h1>

			<p class="mx-auto mt-6 max-w-xl text-lg leading-8 text-slate-600 dark:text-slate-400">
				{description}
			</p>

			<div class="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
				<a href={primaryCta.href}>
					<Button size="lg" class="group h-12 px-8 text-base font-semibold shadow-lg transition-all duration-300 hover:shadow-xl hover:scale-105">
						{primaryCta.text}
						<ArrowRight class="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
					</Button>
				</a>
				<a href={secondaryCta.href}>
					<Button variant="outline" size="lg" class="h-12 px-8 text-base font-semibold transition-all duration-300 hover:bg-slate-50 dark:hover:bg-slate-800">
						{secondaryCta.text}
					</Button>
				</a>
			</div>

			{#if kpis.length > 0}
				<div class="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-3">
					{#each kpis as kpi}
						<div class="flex flex-col items-center">
							<div class="text-3xl font-bold text-slate-900 dark:text-slate-100">
								{kpi.value}
							</div>
							<div class="mt-2 text-sm text-slate-600 dark:text-slate-400">
								{kpi.label}
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</section>
