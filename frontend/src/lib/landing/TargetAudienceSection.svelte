<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Building2, Briefcase, TrendingUp } from 'lucide-svelte';

	const audiences = [
		{
			icon: Building2,
			title: 'Gérant SCI indépendant',
			description:
				'Vous gérez 1 à 3 SCI et cherchez un outil simple pour centraliser loyers, charges et documents sans tableur.',
			badge: 'Particulier'
		},
		{
			icon: Briefcase,
			title: 'Cabinet comptable',
			description:
				'Vous gérez les SCI de vos clients et avez besoin de données structurées, export fiscal et suivi multi-entités.',
			badge: 'Professionnel'
		},
		{
			icon: TrendingUp,
			title: 'Investisseur patrimonial',
			description:
				'Vous optimisez un portefeuille immobilier et voulez des KPIs, alertes et une vision consolidée de vos SCI.',
			badge: 'Investisseur'
		}
	];
</script>

<section class="bg-white py-20 dark:bg-slate-900">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="mb-12 text-center">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Pour qui ?</Badge>
			<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
				Conçu pour ceux qui gèrent des SCI au quotidien
			</h2>
		</div>

		<div class="grid gap-8 md:grid-cols-3">
			{#each audiences as audience}
				<Card class="rounded-2xl border-slate-200 dark:border-slate-700">
					<CardHeader>
						<div
							class="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900/30"
						>
							<audience.icon class="h-6 w-6 text-blue-600 dark:text-blue-400" />
						</div>
						<Badge variant="outline" class="w-fit text-xs">{audience.badge}</Badge>
						<CardTitle class="text-xl">{audience.title}</CardTitle>
					</CardHeader>
					<CardContent>
						<p class="text-slate-600 dark:text-slate-400">{audience.description}</p>
					</CardContent>
				</Card>
			{/each}
		</div>
	</div>
</section>
