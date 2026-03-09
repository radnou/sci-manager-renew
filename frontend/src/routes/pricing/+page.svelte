<script lang="ts">
	import { addToast } from '$lib/components/ui/toast';
	import { createCheckoutSession, type PlanKey } from '$lib/api';
	import { Check, Shield, Zap, Users } from 'lucide-svelte';

	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardFooter,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import HeroSection from '$lib/components/HeroSection.svelte';
	import FeatureCard from '$lib/components/FeatureCard.svelte';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';

	type Plan = {
		planKey: PlanKey;
		name: string;
		price: string;
		billing: string;
		description: string;
		features: string[];
		mode: 'subscription' | 'payment';
		highlight?: boolean;
		popular?: boolean;
	};

	const plans: Plan[] = [
		{
			planKey: 'starter',
			name: 'Starter',
			price: '19€',
			billing: '/mois',
			description: 'Pour démarrer avec un portefeuille compact.',
			features: [
				'1 SCI maximum',
				"Jusqu'à 5 biens",
				'Dashboard KPI (biens + loyers)',
				'Génération de quittance PDF',
				'Suivi des loyers avec statuts'
			],
			mode: 'subscription'
		},
		{
			planKey: 'pro',
			name: 'Pro',
			price: '49€',
			billing: '/mois',
			description: 'Pour les SCI actives avec plusieurs actifs.',
			features: [
				"Jusqu'à 10 SCI",
				"Jusqu'à 20 biens",
				'Contexte multi-SCI',
				'Filtres loyers (date + statut)',
				'Accès prioritaire aux évolutions produit'
			],
			mode: 'subscription',
			highlight: true,
			popular: true
		},
		{
			planKey: 'lifetime',
			name: 'Lifetime',
			price: '299€',
			billing: 'paiement unique',
			description: 'Paiement unique pour un accès durable.',
			features: [
				'Tout le plan Pro',
				'SCI illimitées',
				'Biens illimités',
				'Accès à vie',
				'Mises à jour incluses',
				'Support email prioritaire'
			],
			mode: 'payment'
		}
	];

	let activeCheckout = $state<PlanKey | null>(null);

	async function handleCheckout(plan: Plan) {
		activeCheckout = plan.planKey;
		try {
			const { url } = await createCheckoutSession({
				plan_key: plan.planKey,
				mode: plan.mode
			});
			window.location.href = url;
		} catch (error) {
			const message = formatApiErrorMessage(error, 'Impossible de démarrer le checkout Stripe.');
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

<svelte:head>
	<title>Tarifs — GererSCI</title>
	<meta name="description" content="Offres et abonnements pour gérer vos SCI." />
</svelte:head>

<main class="min-h-screen">
	<HeroSection
		title="Tarifs transparents"
		subtitle="pour une croissance durable"
		description="Choisissez une offre alignée sur votre volume de biens et activez-la immédiatement via Stripe."
		primaryCta={{ text: "Commencer l'essai gratuit", href: '/register' }}
		secondaryCta={{ text: 'Voir les fonctionnalités', href: '#features' }}
		badges={['Activation immédiate', 'Sans engagement']}
		kpis={[
			{ value: '3', label: 'modules coeur: biens, loyers, quittances' },
			{ value: '1', label: 'checkout unifié Stripe' },
			{ value: '24/7', label: 'accès plateforme' }
		]}
	/>

	<!-- Pricing Section -->
	<section class="bg-card py-24">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="mb-16 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium"
					>Stratégie tarifaire</Badge
				>
				<h2 class="mb-4 text-3xl font-bold text-foreground sm:text-4xl">
					Trois offres pour tous les profils
				</h2>
				<p class="mx-auto max-w-2xl text-lg text-muted-foreground">
					Du solopreneur avec quelques biens à l'opérateur multi-actifs, trouvez l'offre qui
					accélère votre croissance.
				</p>
			</div>

			<div class="mx-auto grid max-w-5xl gap-8 lg:grid-cols-3">
				{#each plans as plan (plan.planKey)}
					<Card
						class={`relative overflow-hidden transition-all duration-300 hover:shadow-xl ${
							plan.highlight ? 'scale-105 shadow-lg ring-2 ring-ds-accent' : 'hover:shadow-lg'
						} ${plan.popular ? 'border-ds-accent/30' : ''}`}
					>
						{#if plan.popular}
							<div class="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 transform">
								<Badge
									class="bg-ds-accent px-4 py-1 text-xs font-semibold text-ds-accent-foreground"
								>
									LE PLUS POPULAIRE
								</Badge>
							</div>
						{/if}

						<CardHeader class="pb-4 text-center">
							<CardTitle class="text-2xl font-bold text-foreground">
								{plan.name}
							</CardTitle>
							<CardDescription class="text-muted-foreground">
								{plan.description}
							</CardDescription>
							<div class="mt-4">
								<span class="text-4xl font-bold text-foreground">
									{plan.price}
								</span>
								<span class="ml-1 text-lg text-muted-foreground">
									{plan.billing}
								</span>
							</div>
						</CardHeader>

						<CardContent class="space-y-4">
							<ul class="space-y-3">
								{#each plan.features as feature (feature)}
									<li class="flex items-start gap-3">
										<Check class="mt-0.5 h-5 w-5 flex-shrink-0 text-ds-success" />
										<span class="text-sm leading-relaxed text-muted-foreground">
											{feature}
										</span>
									</li>
								{/each}
							</ul>
						</CardContent>

						<CardFooter class="pt-6">
							<Button
								class={`h-12 w-full text-base font-semibold transition-all duration-300 ${
									plan.highlight
										? 'bg-ds-accent text-ds-accent-foreground shadow-lg hover:bg-ds-accent-hover hover:shadow-xl'
										: 'border-2 border-border bg-card hover:border-ds-accent'
								}`}
								disabled={activeCheckout === plan.planKey}
								onclick={() => handleCheckout(plan)}
							>
								{activeCheckout === plan.planKey
									? 'Redirection en cours...'
									: `Choisir ${plan.name}`}
							</Button>
						</CardFooter>
					</Card>
				{/each}
			</div>

			<!-- Beta support -->
			<div class="mt-12 text-center">
				<div
					class="inline-flex items-center gap-2 rounded-full border border-ds-success/30 bg-ds-success-soft px-4 py-2"
				>
					<Shield class="h-4 w-4 text-ds-success" />
					<span class="text-sm font-medium text-ds-success">
						Phase beta: onboarding guide et support email
					</span>
				</div>
			</div>
		</div>
	</section>

	<!-- Features Comparison -->
	<section id="features" class="py-24">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="mb-16 text-center">
				<h2 class="mb-4 text-3xl font-bold text-foreground sm:text-4xl">
					Pourquoi choisir GererSCI ?
				</h2>
				<p class="mx-auto max-w-2xl text-lg text-muted-foreground">
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

	<!-- Use Cases -->
	<section class="mx-auto mt-20 max-w-5xl px-4">
		<p class="sci-eyebrow text-center">Cas d'usage concrets</p>
		<h2 class="mt-3 text-center text-2xl font-semibold text-foreground">
			Conçu pour les gérants de SCI
		</h2>
		<div class="mt-10 grid gap-6 md:grid-cols-3">
			<div class="rounded-2xl border border-border bg-card p-6">
				<p class="text-sm font-semibold text-ds-accent">Gérant solo</p>
				<p class="mt-3 text-sm leading-relaxed text-muted-foreground">
					Marc gère 2 SCI familiales. Il génère ses quittances en un clic et suit ses loyers sans
					tableur. Le calcul fiscal simplifié lui fait gagner une demi-journée par trimestre.
				</p>
			</div>
			<div class="rounded-2xl border border-border bg-card p-6">
				<p class="text-sm font-semibold text-ds-accent">Cabinet comptable</p>
				<p class="mt-3 text-sm leading-relaxed text-muted-foreground">
					Le cabinet Durand accompagne 15 SCI. Chaque associé accède à son portefeuille, le cabinet
					centralise la conformité documentaire et les échéances fiscales depuis un dashboard
					consolidé.
				</p>
			</div>
			<div class="rounded-2xl border border-border bg-card p-6">
				<p class="text-sm font-semibold text-ds-accent">Opérateur patrimonial</p>
				<p class="mt-3 text-sm leading-relaxed text-muted-foreground">
					Patrimonia pilote 8 SCI en exploitation. Le dashboard consolide le cashflow mensuel, les
					taux de recouvrement et les alertes de loyers impayés pour arbitrer rapidement.
				</p>
			</div>
		</div>
	</section>

	<!-- FAQ Section -->
	<section class="py-24">
		<div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
			<div class="mb-16 text-center">
				<h2 class="mb-4 text-3xl font-bold text-foreground sm:text-4xl">Questions fréquentes</h2>
			</div>

			<div class="space-y-6">
				<div class="rounded-lg border border-border bg-card p-6 shadow-sm">
					<h3 class="mb-2 text-lg font-semibold text-foreground">
						Puis-je changer de plan à tout moment ?
					</h3>
					<p class="text-muted-foreground">
						Oui. En phase beta, le changement de plan est traite rapidement via le support, puis
						applique sur votre abonnement Stripe.
					</p>
				</div>

				<div class="rounded-lg border border-border bg-card p-6 shadow-sm">
					<h3 class="mb-2 text-lg font-semibold text-foreground">
						Y a-t-il un engagement minimum ?
					</h3>
					<p class="text-muted-foreground">
						Non, nos abonnements sont mensuels sans engagement. Vous pouvez résilier à tout moment.
					</p>
				</div>

				<div class="rounded-lg border border-border bg-card p-6 shadow-sm">
					<h3 class="mb-2 text-lg font-semibold text-foreground">
						Les données sont-elles sécurisées ?
					</h3>
					<p class="text-muted-foreground">
						Les flux passent en HTTPS, les paiements sont traites par Stripe et les donnees
						applicatives sont hebergees sur Supabase avec controles d'acces.
					</p>
				</div>
			</div>
		</div>
	</section>
</main>
