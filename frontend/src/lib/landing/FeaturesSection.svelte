<script lang="ts">
	import { Landmark, FileText, Users, Calculator, Shield, Bell } from '@lucide/svelte';

	const features = [
		{
			icon: Landmark,
			title: 'Gestion multi-SCI',
			description: 'Centralisez toutes vos SCI en un seul tableau de bord.'
		},
		{
			icon: FileText,
			title: 'Quittances automatiques',
			description: 'Générez et envoyez vos quittances en un clic.'
		},
		{
			icon: Users,
			title: 'Gestion des associés',
			description: 'Suivez les parts, les distributions et les décisions.'
		},
		{
			icon: Calculator,
			title: 'Déclarations fiscales',
			description: '2072, 2065, CERFA 2044 — tout est pré-rempli.'
		},
		{
			icon: Shield,
			title: 'Sécurité bancaire',
			description: 'Vos données sont chiffrées et sécurisées (RGPD).'
		},
		{
			icon: Bell,
			title: 'Alertes intelligentes',
			description: 'Ne manquez plus aucune échéance (loyers, AG, impôts).'
		}
	];
</script>

<section id="features" class="bg-slate-50 py-20 dark:bg-slate-950">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="mx-auto max-w-2xl text-center">
			<h2 class="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl dark:text-white">
				Tout ce qu'il faut pour gérer votre SCI
			</h2>
			<p class="mt-4 text-lg text-slate-600 dark:text-slate-300">
				Des outils pensés pour les propriétaires, pas les comptables.
			</p>
		</div>
		<div class="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
			{#each features as feature}
				<div class="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
					<div class="mb-4 inline-flex rounded-lg bg-blue-50 p-3 dark:bg-blue-950">
						<feature.icon class="h-6 w-6 text-blue-600 dark:text-blue-400" />
					</div>
					<h3 class="text-lg font-semibold text-slate-900 dark:text-white">{feature.title}</h3>
					<p class="mt-2 text-slate-600 dark:text-slate-300">{feature.description}</p>
				</div>
			{/each}
		</div>
	</div>
</section>
