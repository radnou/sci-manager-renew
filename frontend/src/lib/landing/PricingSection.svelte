<script lang="ts">
	import { Button } from "$lib/components/ui/button";
	import { Check, Loader2 } from "lucide-svelte";
	import type { PlanInfo } from "$lib/config/plans";
	import { formatPrice, formatPeriod, formatPriceTTC } from "$lib/config/plans";

	interface Props {
		plans: (PlanInfo & { href: string | null })[];
		billingPeriod: "month" | "year";
		checkoutLoading: string | null;
		openCheckoutModal: (planKey: string) => void;
	}

	let { plans, billingPeriod = $bindable(), checkoutLoading, openCheckoutModal }: Props = $props();
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
			
			<!-- Period toggle -->
			<div class="mt-6 flex items-center justify-center gap-4">
				<button
					type="button"
					onclick={() => { billingPeriod = 'month'; }}
					class="text-sm font-semibold transition-colors {billingPeriod === 'month' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'}"
				>
					Mensuel
				</button>
				<button
					type="button"
					onclick={() => { billingPeriod = billingPeriod === 'month' ? 'year' : 'month'; }}
					class="relative rounded-full bg-slate-200 p-1 transition-colors dark:bg-slate-800"
					aria-label="Billing Period Toggle"
				>
					<span
						class="block h-5 w-10 rounded-full bg-white transition-transform dark:bg-slate-950 {billingPeriod === 'year' ? 'translate-x-5' : 'translate-x-0'}"
					></span>
				</button>
				<button
					type="button"
					onclick={() => { billingPeriod = 'year'; }}
					class="text-sm font-semibold transition-colors {billingPeriod === 'year' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'}"
				>
					Annuel <span class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300">Option 2 mois gratuits</span>
				</button>
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
					<div class="mt-4 flex flex-col">
						<div class="flex items-baseline">
							<span class="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">
								{formatPrice(plan, billingPeriod)}
							</span>
							<span class="ml-1 text-sm text-slate-500 dark:text-slate-400">
								{formatPeriod(billingPeriod)}
							</span>
						</div>
						<span class="mt-1 text-xs text-slate-400 dark:text-slate-500">
							{formatPriceTTC(plan, billingPeriod)}
						</span>
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
						<Button
							variant={plan.popular ? 'default' : 'outline'}
							class="w-full focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
							onclick={() => openCheckoutModal(plan.key)}
							disabled={checkoutLoading !== null}
						>
							{#if checkoutLoading === plan.key}
								<Loader2 class="h-4 w-4 animate-spin mr-2" />
							{/if}
							{plan.cta}
						</Button>
					</div>
				</div>
			{/each}
		</div>
	</div>
</section>
