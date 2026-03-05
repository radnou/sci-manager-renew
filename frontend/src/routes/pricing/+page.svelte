<script lang="ts">
	import { addToast } from '$lib/components/ui/toast';
	import { createCheckoutSession } from '$lib/api';
	import { Check, Users, Shield, Zap } from 'lucide-svelte';

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
			description: 'Pour démarrer avec un portefeuille compact.',
			features: [
				"Jusqu'à 5 biens",
				'Dashboard KPI (biens + loyers)',
				'Génération de quittance PDF',
				'Suivi des loyers avec statuts'
			],
			priceId: stripeStarterPriceId,
			mode: 'subscription'
		},
		{
			name: 'Pro',
			price: '49€',
			billing: '/mois',
			description: 'Pour les SCI actives avec plusieurs actifs.',
			features: [
				'Biens illimités',
				'Contexte multi-SCI',
				'Filtres loyers (date + statut)',
				'Accès prioritaire aux évolutions produit'
			],
			priceId: stripeProPriceId,
			mode: 'subscription',
			highlight: true,
			popular: true
		},
		{
			name: 'Lifetime',
			price: '299€',
			billing: 'paiement unique',
			description: 'Paiement unique pour un accès durable.',
			features: ['Tout le plan Pro', 'Accès à vie', 'Mises à jour incluses', 'Support email prioritaire'],
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
		description="Choisissez une offre alignée sur votre volume de biens et activez-la immédiatement via Stripe."
		primaryCta={{ text: "Commencer l'essai gratuit", href: "/register" }}
		secondaryCta={{ text: "Voir les fonctionnalités", href: "#features" }}
		badges={['Activation immédiate', 'Sans engagement']}
		kpis={[
			{ value: '3', label: 'modules coeur: biens, loyers, quittances' },
			{ value: '1', label: 'checkout unifié Stripe' },
			{ value: '24/7', label: 'accès plateforme' }
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

			<!-- Beta support -->
			<div class="text-center mt-12">
				<div class="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-full border border-emerald-200 dark:border-emerald-800">
					<Shield class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
					<span class="text-sm font-medium text-emerald-700 dark:text-emerald-300">
						Phase beta: onboarding guide et support email
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
					Pourquoi choisir GererSCI ?
				</h2>
				<p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
					Une base opérationnelle claire pour piloter votre SCI sans Excel dispersé.
				</p>
			</div>

			<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
				<FeatureCard
					icon={Zap}
					title="Exécution rapide"
					description="Saisie structurée des biens et loyers, avec indicateurs mis à jour en continu."
					badge="Temps gagné"
				/>
				<FeatureCard
					icon={Shield}
					title="Sécurité opérationnelle"
					description="Authentification Supabase, séparation des données par SCI et journalisation backend."
					badge="Sécurité"
				/>
				<FeatureCard
					icon={Users}
					title="Multi-SCI en pratique"
					description="Passez d'une SCI à l'autre depuis le cockpit et conservez une vue claire des flux."
					badge="Pilotage"
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
					quote="La prise en main est rapide et la vue loyers évite les oublis mensuels."
					author="Thomas Moreau"
					role="Gérant de portefeuille"
					company="Immobilier Plus"
					rating={5}
				/>
				<TestimonialCard
					quote="Le passage de nos tableaux Excel vers un cockpit unique nous simplifie la routine."
					author="Claire Bernard"
					role="Directrice patrimoniale"
					company="Bernard Finance"
					rating={5}
				/>
				<TestimonialCard
					quote="Le checkout est simple et l'équipe produit publie des améliorations régulières."
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
						Oui. En phase beta, le changement de plan est traite rapidement via le support, puis applique sur votre abonnement Stripe.
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
						Les flux passent en HTTPS, les paiements sont traites par Stripe et les donnees applicatives sont hebergees sur Supabase avec controles d'acces.
					</p>
				</div>
			</div>
		</div>
	</section>
</main>
