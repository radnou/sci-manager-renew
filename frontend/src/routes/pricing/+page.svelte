<script lang="ts">
	import { addToast } from '$lib/components/ui/toast';
	import { createCheckoutSession } from '$lib/api';
	import { Check } from 'lucide-svelte';

	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';

	type Plan = {
		name: string;
		price: string;
		billing: string;
		description: string;
		features: string[];
		priceId: string;
		mode: 'subscription' | 'payment';
		highlight?: boolean;
	};

	const stripeStarterPriceId = import.meta.env.VITE_STRIPE_PRICE_STARTER || 'price_starter_placeholder';
	const stripeProPriceId = import.meta.env.VITE_STRIPE_PRICE_PRO || 'price_pro_placeholder';
	const stripeLifetimePriceId = import.meta.env.VITE_STRIPE_PRICE_LIFETIME || 'price_lifetime_placeholder';

	const plans: Plan[] = [
		{
			name: 'Starter',
			price: '19€',
			billing: '/mois',
			description: 'Pour les SCI en phase de croissance.',
			features: ['Jusqu’à 5 biens', 'Compta basique', 'Quitus PDF'],
			priceId: stripeStarterPriceId,
			mode: 'subscription'
		},
		{
			name: 'Pro',
			price: '49€',
			billing: '/mois',
			description: 'Pour opérateurs multi-actifs et partenaires.',
			features: ['Biens illimités', 'Cerfa 2044 auto', 'Simulateur IR/IS', 'Support prioritaire'],
			priceId: stripeProPriceId,
			mode: 'subscription',
			highlight: true
		},
		{
			name: 'Lifetime',
			price: '299€',
			billing: 'paiement unique',
			description: 'Accès à vie pour une acquisition définitive.',
			features: ['Tout le plan Pro', 'Accès à vie', 'Mises à jour incluses'],
			priceId: stripeLifetimePriceId,
			mode: 'payment'
		}
	];

	let activeCheckout = $state<string | null>(null);

	async function handleCheckout(plan: Plan) {
		activeCheckout = plan.priceId;
		try {
			const { url } = await createCheckoutSession({
				price_id: plan.priceId,
				mode: plan.mode
			});
			window.location.href = url;
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Impossible de démarrer le checkout Stripe.';
			addToast({
				title: 'Paiement indisponible',
				description: message,
				variant: 'error'
			});
		} finally {
			activeCheckout = null;
		}
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Monétisation</p>
		<h1 class="sci-page-title">Tarifs SCI Manager</h1>
		<p class="sci-page-subtitle">Choisissez une offre alignée à votre niveau de portefeuille et votre ambition de pilotage.</p>
	</header>

	<div class="grid gap-4 md:grid-cols-3">
		{#each plans as plan (plan.priceId)}
			<Card class={`sci-section-card ${plan.highlight ? 'ring-2 ring-cyan-400/60' : ''}`}>
				<CardHeader>
					<div class="flex items-center justify-between">
						<CardTitle>{plan.name}</CardTitle>
						{#if plan.highlight}
							<Badge variant="success">Le plus choisi</Badge>
						{/if}
					</div>
					<CardDescription>{plan.description}</CardDescription>
					<p class="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
						{plan.price}<span class="ml-2 text-base font-medium text-slate-500">{plan.billing}</span>
					</p>
				</CardHeader>
				<CardContent>
					<ul class="space-y-2 text-sm text-slate-700">
						{#each plan.features as feature (feature)}
							<li class="flex items-center gap-2">
								<Check class="h-4 w-4 text-emerald-600" />
								<span>{feature}</span>
							</li>
						{/each}
					</ul>
				</CardContent>
				<CardFooter>
					<Button
						class="w-full"
						variant={plan.highlight ? 'default' : 'outline'}
						disabled={activeCheckout === plan.priceId}
						onclick={() => handleCheckout(plan)}
					>
						{activeCheckout === plan.priceId ? 'Redirection…' : 'Choisir'}
					</Button>
				</CardFooter>
			</Card>
		{/each}
	</div>
</section>
