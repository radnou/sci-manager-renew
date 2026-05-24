<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Check, Loader2 } from 'lucide-svelte';
	import type { PlanInfo } from '$lib/config/plans';
	import { formatPrice, formatPeriod, formatPriceTTC } from '$lib/config/plans';

	interface Props {
		plans: (PlanInfo & { href: string | null })[];
		billingPeriod: 'month' | 'year';
		checkoutLoading: string | null;
		openCheckoutModal: (planKey: string) => Promise<void>;
	}

	let {
		plans,
		billingPeriod = $bindable(),
		checkoutLoading,
		openCheckoutModal
	}: Props = $props();
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
			<!-- Toggle Period -->
			<div class="mt-8 flex justify-center">
				<div class="relative flex rounded-full bg-slate-100 p-1 dark:bg-slate-800">
					<button
						class="relative flex w-32 items-center justify-center rounded-full py-2 text-sm font-semibold outline-none transition-colors {billingPeriod === 'month' ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-white' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'}"
						onclick={() => (billingPeriod = 'month')}
					>
						Mensuel
					</button>
					<button
						class="relative flex w-32 items-center justify-center rounded-full py-2 text-sm font-semibold outline-none transition-colors {billingPeriod === 'year' ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-white' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'}"
						onclick={() => (billingPeriod = 'year')}
					>
						Annuel
					</button>
				</div>
			</div>
		</div>
		<div class="mt-16 grid gap-8 lg:grid-cols-2 max-w-4xl mx-auto">
			{#each plans as plan}
				<div class="relative rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800 {plan.popular ? 'ring-2 ring-blue-600' : ''}">
					{#if plan.popular}
						<div class="absolute -top-3 left-1/2 -translate-x-1/2">
							<span class="rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white">Populaire</span>
						</div>
					{/if}
					<h3 class="text-lg font-semibold text-slate-900 dark:text-white">{plan.name}</h3>
					<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{plan.description}</p>
					<div class="mt-4 flex flex-col items-start">
						<div class="flex items-baseline">
							<span class="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">{formatPrice(plan, billingPeriod)}</span>
							<span class="ml-1 text-sm text-slate-500 dark:text-slate-400">{formatPeriod(billingPeriod)}</span>
						</div>
						<span class="text-xs text-slate-400 mt-1">{formatPriceTTC(plan, billingPeriod)}</span>
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
						<Button variant={plan.popular ? 'default' : 'outline'} class="w-full" disabled={checkoutLoading === plan.key} onclick={() => openCheckoutModal(plan.key)}>
							{#if checkoutLoading === plan.key}
								<Loader2 class="mr-2 h-4 w-4 animate-spin" />
							{/if}
							{plan.cta}
						</Button>
					</div>
				</div>
			{/each}
		</div>
	</div>
</section>
