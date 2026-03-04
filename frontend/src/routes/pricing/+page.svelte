<script lang="ts">
	import { addToast } from '$lib/components/ui/toast';
	import { createCheckoutSession } from '$lib/api';
	import { Check, Star, Users, Shield, Zap } from 'lucide-svelte';

	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import HeroSection from '$lib/components/HeroSection.svelte';
	import FeatureCard from '$lib/components/FeatureCard.svelte';
	import TestimonialCard from '$lib/components/TestimonialCard.svelte';

	type Plan = {
		name: string;
		price: string;
		billing: string;
		description: string;
		features: string[];
		priceId: string;
		mode: 'subscription' | 'payment';
		highlight?: boolean;
		popular?: boolean;
	};

	const stripeStarterPriceId = import.meta.env.VITE_STRIPE_STARTER_PRICE_ID || 'price_starter_placeholder';
	const stripeProPriceId = import.meta.env.VITE_STRIPE_PRO_PRICE_ID || 'price_pro_placeholder';
	const stripeLifetimePriceId = import.meta.env.VITE_STRIPE_LIFETIME_PRICE_ID || 'price_lifetime_placeholder';

	const plans: Plan[] = [
		{
			name: 'Starter',
			price: '19€',
			billing: '/mois',
			description: 'Pour les SCI en phase de croissance.',
			features: ['Jusqu\'à 5 biens', 'Compta basique', 'Quitus PDF', 'Support email'],
			priceId: stripeStarterPriceId,
			mode: 'subscription'
		},
		{
			name: 'Pro',
			price: '49€',
			billing: '/mois',
			description: 'Pour opérateurs multi-actifs et partenaires.',
			features: ['Biens illimités', 'Cerfa 2044 auto', 'Simulateur IR/IS', 'Support prioritaire', 'API access', 'Reporting avancé'],
			priceId: stripeProPriceId,
			mode: 'subscription',
			highlight: true,
			popular: true
		},
		{
			name: 'Lifetime',
			price: '299€',
			billing: 'paiement unique',
			description: 'Accès à vie pour une acquisition définitive.',
			features: ['Tout le plan Pro', 'Accès à vie', 'Mises à jour incluses', 'Support VIP', 'Formation personnalisée'],
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

<main class="min-h-screen bg-slate-50 dark:bg-slate-950">
	<HeroSection
		title="Tarifs transparents"
		subtitle="pour une croissance durable"
		description="Des prix justes pour des fonctionnalités premium. Choisissez l'offre qui correspond à votre portefeuille immobilier et évoluez quand vous voulez."
		primaryCta={{ text: "Commencer l'essai gratuit", href: "/register" }}
		secondaryCta={{ text: "Voir les fonctionnalités", href: "#features" }}
		badges={["14 jours gratuit", "Sans engagement"]}
		kpis={[
			{ value: "ROI 280%", label: "en moyenne sur 3 ans" },
			{ value: "85%", label: "des clients renouvellent" },
			{ value: "5 min", label: "pour onboarder un bien" }
		]}
	/>

	<!-- Pricing Section -->
	<section class="py-24 bg-white dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center mb-16">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Stratégie tarifaire</Badge>
				<h2 class="text-3xl font-bold text-slate-900 dark:text-slate-100 sm:text-4xl mb-4">
					Trois offres pour tous les profils
				</h2>
				<p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
					Du solopreneur avec quelques biens à l'opérateur multi-actifs, trouvez l'offre qui accélère votre croissance.
				</p>
			</div>

			<div class="grid gap-8 lg:grid-cols-3 max-w-5xl mx-auto">
				{#each plans as plan (plan.priceId)}
					<Card class={`relative overflow-hidden transition-all duration-300 hover:shadow-xl ${
						plan.highlight ? 'ring-2 ring-blue-500 shadow-lg scale-105' : 'hover:shadow-lg'
					} ${plan.popular ? 'border-blue-200 dark:border-blue-800' : ''}`}>
						{#if plan.popular}
							<div class="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
								<Badge class="bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-4 py-1 text-xs font-semibold">
									LE PLUS POPULAIRE
								</Badge>
							</div>
						{/if}

						<CardHeader class="text-center pb-4">
							<CardTitle class="text-2xl font-bold text-slate-900 dark:text-slate-100">
								{plan.name}
							</CardTitle>
							<CardDescription class="text-slate-600 dark:text-slate-400">
								{plan.description}
							</CardDescription>
							<div class="mt-4">
								<span class="text-4xl font-bold text-slate-900 dark:text-slate-100">
									{plan.price}
								</span>
								<span class="text-lg text-slate-500 dark:text-slate-400 ml-1">
									{plan.billing}
								</span>
							</div>
						</CardHeader>

						<CardContent class="space-y-4">
							<ul class="space-y-3">
								{#each plan.features as feature (feature)}
									<li class="flex items-start gap-3">
										<Check class="h-5 w-5 text-emerald-500 mt-0.5 flex-shrink-0" />
										<span class="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">
											{feature}
										</span>
									</li>
								{/each}
							</ul>
						</CardContent>

						<CardFooter class="pt-6">
							<Button
								class={`w-full h-12 text-base font-semibold transition-all duration-300 ${
									plan.highlight
										? 'bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white shadow-lg hover:shadow-xl'
										: 'bg-white dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-400'
								}`}
								disabled={activeCheckout === plan.priceId}
								onclick={() => handleCheckout(plan)}
							>
								{activeCheckout === plan.priceId ? 'Redirection en cours...' : `Choisir ${plan.name}`}
							</Button>
						</CardFooter>
					</Card>
				{/each}
			</div>

			<!-- Money-back guarantee -->
			<div class="text-center mt-12">
				<div class="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-full border border-emerald-200 dark:border-emerald-800">
					<Shield class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
					<span class="text-sm font-medium text-emerald-700 dark:text-emerald-300">
						Garantie satisfait ou remboursé • 30 jours
					</span>
				</div>
			</div>
		</div>
	</section>

	<!-- Features Comparison -->
	<section id="features" class="py-24 bg-slate-50 dark:bg-slate-950">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center mb-16">
				<h2 class="text-3xl font-bold text-slate-900 dark:text-slate-100 sm:text-4xl mb-4">
					Pourquoi choisir SCI Manager ?
				</h2>
				<p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
					Des fonctionnalités pensées pour les professionnels de l'immobilier, validées par des experts Big4.
				</p>
			</div>

			<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
				<FeatureCard
					icon={Zap}
					title="Automatisation intelligente"
					description="Relances automatiques, génération de CERFA 2044, et workflows personnalisables pour gagner du temps."
					badge="Temps gagné"
				/>
				<FeatureCard
					icon={Shield}
					title="Conformité garantie"
					description="Mises à jour automatiques des normes comptables et réglementaires. Jamais de retard sur la compliance."
					badge="Sécurité"
				/>
				<FeatureCard
					icon={Users}
					title="Écosystème intégré"
					description="Connexions natives avec votre comptable, notaire et partenaires. Un écosystème complet."
					badge="Intégration"
				/>
			</div>
		</div>
	</section>

	<!-- Testimonials -->
	<section class="py-24 bg-white dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center mb-16">
				<h2 class="text-3xl font-bold text-slate-900 dark:text-slate-100 sm:text-4xl mb-4">
					Ils nous font confiance
				</h2>
				<p class="text-lg text-slate-600 dark:text-slate-400">
					Des retours d'utilisateurs qui comptent dans l'écosystème immobilier
				</p>
			</div>

			<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
				<TestimonialCard
					quote="Le plan Pro a transformé notre gestion. Nous avons réduit nos impayés de 60% et gagné 8h par semaine."
					author="Thomas Moreau"
					role="Gérant de portefeuille"
					company="Immobilier Plus"
					rating={5}
				/>
				<TestimonialCard
					quote="Enfin un outil qui comprend les spécificités des SCI familiales. L'interface est intuitive et les fonctionnalités complètes."
					author="Claire Bernard"
					role="Directrice patrimoniale"
					company="Bernard Finance"
					rating={5}
				/>
				<TestimonialCard
					quote="Le lifetime était le meilleur investissement. Payé une fois, utilisé tous les jours. ROI exceptionnel."
					author="Marc Dubois"
					role="Opérateur immobilier"
					company="Dubois Patrimoine"
					rating={5}
				/>
			</div>
		</div>
	</section>

	<!-- FAQ Section -->
	<section class="py-24 bg-slate-50 dark:bg-slate-950">
		<div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
			<div class="text-center mb-16">
				<h2 class="text-3xl font-bold text-slate-900 dark:text-slate-100 sm:text-4xl mb-4">
					Questions fréquentes
				</h2>
			</div>

			<div class="space-y-6">
				<div class="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
						Puis-je changer de plan à tout moment ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Oui, vous pouvez upgrader ou downgrader votre plan à tout moment. Les changements sont effectifs immédiatement.
					</p>
				</div>

				<div class="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
						Y a-t-il un engagement minimum ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Non, nos abonnements sont mensuels sans engagement. Vous pouvez résilier à tout moment.
					</p>
				</div>

				<div class="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
						Les données sont-elles sécurisées ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Absolument. Nous utilisons le chiffrement de bout en bout et respectons le RGPD. Vos données financières sont en sécurité.
					</p>
				</div>
			</div>
		</div>
	</section>
</main>
