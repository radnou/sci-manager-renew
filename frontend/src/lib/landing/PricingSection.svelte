<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Check } from '@lucide/svelte';
	import { goto } from '$app/navigation';

	const plans = [
		{
			name: 'Gratuit',
			price: '0€',
			period: '/mois',
			description: 'Pour découvrir',
			features: ['1 SCI', '1 bien', 'Quittances manuelles', 'Support email'],
			cta: 'Commencer',
			popular: false
		},
		{
			name: 'Starter',
			price: '19€',
			period: '/mois',
			description: 'Pour les petits propriétaires',
			features: ['3 SCI', '5 biens', 'Quittances auto', 'Déclarations fiscales', 'Support prioritaire'],
			cta: 'Essayer 14 jours',
			popular: true
		},
		{
			name: 'Pro',
			price: '49€',
			period: '/mois',
			description: 'Pour les investisseurs',
			features: ['SCI illimitées', 'Biens illimités', 'API + Webhooks', 'Multi-utilisateurs', 'Support dédié'],
			cta: 'Contacter',
			popular: false
		}
	];
</script>

<section id="pricing" class="bg-slate-50 py-20 dark:bg-slate-950">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="mx-auto max-w-2xl text-center">
			<h2 class="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl dark:text-white">
				Des tarifs simples
			</h2>
			<p class="mt-4 text-lg text-slate-600 dark:text-slate-300">
				Commencez gratuitement, upgradez quand vous voulez.
			</p>
		</div>
		<div class="mt-16 grid gap-8 lg:grid-cols-3">
			{#each plans as plan}
				<div class="relative rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 {plan.popular ? 'ring-2 ring-blue-600' : ''}">
					{#if plan.popular}
						<div class="absolute -top-3 left-1/2 -translate-x-1/2">
							<span class="rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white">Populaire</span>
						</div>
					{/if}
					<h3 class="text-lg font-semibold text-slate-900 dark:text-white">{plan.name}</h3>
					<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{plan.description}</p>
					<div class="mt-4 flex items-baseline">
						<span class="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">{plan.price}</span>
						<span class="ml-1 text-sm text-slate-500 dark:text-slate-400">{plan.period}</span>
					</div>
					<ul class="mt-6 space-y-3">
						{#each plan.features as feature}
							<li class="flex items-start gap-2">
								<Check class="h-5 w-5 shrink-0 text-blue-600 dark:text-blue-400" />
								<span class="text-sm text-slate-600 dark:text-slate-300">{feature}</span>
							</li>
						{/each}
					</ul>
					<div class="mt-8">
						<Button variant={plan.popular ? 'default' : 'outline'} class="w-full" onclick={() => goto('/login')}>
							{plan.cta}
						</Button>
					</div>
				</div>
			{/each}
		</div>
	</div>
</section>
