<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
	import {
		Building2,
		FileText,
		TrendingUp,
		Shield,
		Users,
		Calculator,
		Check,
		ArrowRight,
		Briefcase,
		BarChart3,
		ChevronDown,
		ChevronUp,
		Loader2
	} from 'lucide-svelte';
	import { API_URL } from '$lib/api';

	let billingPeriod = $state<'month' | 'year'>('month');
	let checkoutLoading = $state<string | null>(null);
	let openFaqIndex = $state<number | null>(null);
	const featureSections = [
		{
			eyebrow: 'Gestion des biens',
			title: "Vos biens en un coup d'oeil",
			description:
				'Grille visuelle avec statut locatif, loyer mensuel et rendement brut. Ajoutez un bien en 30 secondes.',
			image: '/images/showcase/biens-grid.png',
			alt: 'Grille des biens immobiliers — statut Loue, loyer, rendement',
			bullets: [
				'Statut locatif en temps reel',
				'Rendement brut calcule',
				'Actions rapides : modifier, quittance'
			]
		},
		{
			eyebrow: 'Vision financiere',
			title: 'Revenus, charges et cashflow consolides',
			description:
				'Vue transversale de toutes vos SCI. Evolution mensuelle, repartition par SCI, export CSV en 1 clic.',
			image: '/images/showcase/finances-consolidated.png',
			alt: 'Vue financiere consolidee — revenus, charges, cashflow net',
			bullets: ['Cashflow net par periode', 'Repartition par SCI', 'Export comptable CSV']
		},
		{
			eyebrow: 'Gouvernance',
			title: 'Associes et parts sociales',
			description:
				"Gerez vos associes, leurs parts et roles. Total automatique avec alerte si \u2260 100%.",
			image: '/images/showcase/fiche-identite.png',
			alt: 'Page associes — parts sociales, roles, total 100%',
			bullets: [
				'Parts et pourcentages',
				"Roles gerant / associe",
				'Invitation par email'
			]
		},
		{
			eyebrow: 'Fiscalite',
			title: 'Generez votre CERFA 2044 en un clic',
			description:
				"Exercices fiscaux IR et IS, resultat fiscal calcule, declaration PDF prete a deposer.",
			image: '/images/showcase/loyers-with-button.png',
			alt: 'Page fiscalite — exercices, CERFA 2044, resultat fiscal',
			bullets: [
				'Regimes IR et IS',
				'PDF CERFA 2044 automatique',
				'Resultat fiscal calcule'
			]
		}
	];

	// Lightbox state
	let lightboxOpen = $state(false);
	let lightboxIndex = $state(0);

	const allImages = [
		{ src: '/images/showcase/dashboard-light.png', title: 'Dashboard' },
		...featureSections.map((f) => ({ src: f.image, title: f.eyebrow }))
	];

	function openLightbox(index: number) {
		lightboxIndex = index;
		lightboxOpen = true;
	}

	function closeLightbox() {
		lightboxOpen = false;
	}

	function nextImage() {
		lightboxIndex = (lightboxIndex + 1) % allImages.length;
	}

	function prevImage() {
		lightboxIndex = (lightboxIndex - 1 + allImages.length) % allImages.length;
	}

	async function createGuestCheckout(planKey: string) {
		checkoutLoading = planKey;
		try {
			const res = await fetch(`${API_URL}/api/v1/stripe/create-guest-checkout`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ plan_key: planKey, billing_period: billingPeriod })
			});
			const data = await res.json();
			if (data.url) {
				window.location.href = data.url;
			}
		} catch {
			window.location.href = `/register?plan=${planKey}`;
		} finally {
			checkoutLoading = null;
		}
	}

	const studyReferences = [
		{
			title: 'Impayés locatifs en France (2025)',
			finding:
				"Le taux d'impayés moyen est estimé à 3,50%, avec une amélioration nette pour les acteurs qui industrialisent la gestion.",
			source: 'Lamy Immobilier',
			url: 'https://www.lamy-immobilier.fr/le-guide-immo/louer-son-logement/les-impayes-de-loyer-en-france-la-situation-en-2025'
		},
		{
			title: 'Impact de la gestion professionnelle',
			finding:
				"Les données consolidées montrent 1,97% d'impayés en gestion professionnelle contre 5,33% en gestion directe.",
			source: 'FNPR',
			url: 'https://www.fnpr.fr/loyers-impayes-en-2025-comprendre-anticiper-et-securiser-vos-revenus/'
		},
		{
			title: 'Temps administratif des gestionnaires',
			finding:
				"Jusqu'à 50% du temps peut être absorbé par des tâches répétitives, d'où un fort ROI de l'automatisation ciblée.",
			source: 'Euodia (étude McKinsey)',
			url: 'https://www.euodia.fr/blog/digitalisation-impacts-gestion-actifs/'
		},
		{
			title: 'Productivité après digitalisation',
			finding:
				'72% des directions immobilières indiquent une amélioration notable dans les 12 mois.',
			source: 'Septeo (enquête Deloitte 2024)',
			url: 'https://www.septeo.com/fr/articles/cinq-chiffres-cles-sur-la-digitalisation-du-marche-immobilier'
		},
		{
			title: 'Risque réglementaire SCI',
			finding:
				"Le non-respect de l'encadrement des loyers peut entraîner jusqu'à 15000 EUR de sanctions pour une personne morale.",
			source: 'Crédit Agricole e-immobilier',
			url: 'https://e-immobilier.credit-agricole.fr/conseils/reglementation/bailleurs-locataires-coproprietaires-les-nouveautes-de-la-loi-elan'
		},
		{
			title: 'KPI de gestion locative',
			finding:
				'Recouvrement >98%, vacance proche de 5% et suivi du délai de paiement sont les standards les plus suivis sur le marché.',
			source: 'Lockimmo / CAFPI / Manda',
			url: 'https://www.lockimmo.com/les-indicateurs-cles-pour-piloter-la-rentabilite-de-votre-portefeuille-de-gestion-locative/'
		}
	];

	const features = [
		{
			icon: FileText,
			title: 'Quittances PDF automatiques',
			description:
				'Générez vos quittances de loyer en PDF, téléchargeables immédiatement. Fini les modèles Word bricolés.',
			color: 'cyan'
		},
		{
			icon: Calculator,
			title: 'Résumé fiscal par exercice',
			description:
				'Calcul automatique du résultat foncier (revenus − charges). Export PDF simplifié pour préparer votre déclaration.',
			color: 'amber'
		},
		{
			icon: BarChart3,
			title: 'Suivi des retards de paiement',
			description:
				'Visualisez les loyers impayés depuis votre tableau de bord. Ne laissez plus un retard passer inaperçu.',
			color: 'blue'
		},
		{
			icon: Building2,
			title: 'Toutes vos SCI en un seul compte',
			description:
				'Gérez plusieurs SCI depuis une seule interface. Biens, loyers, associés et charges centralisés par structure.',
			color: 'emerald'
		}
	];

	const plans = [
		{
			key: 'free',
			name: 'Essentiel',
			description: 'Pour démarrer avec une petite SCI',
			monthlyPrice: 0,
			yearlyPrice: 0,
			popular: false,
			features: [
				'1 SCI',
				'2 biens maximum',
				'Suivi des loyers',
				'Suivi des charges',
				'Quittances PDF'
			],
			cta: 'Commencer gratuitement',
			href: '/register'
		},
		{
			key: 'starter',
			name: 'Gestion',
			description: 'Pour les gérants actifs avec plusieurs biens',
			monthlyPrice: 19,
			yearlyPrice: 180,
			popular: false,
			features: [
				'3 SCI',
				'10 biens maximum',
				'Gestion documentaire',
				'Notifications email',
				'Gestion des associés',
				'Assurance PNO & frais agence',
				'Support email prioritaire'
			],
			cta: 'Choisir Gestion',
			href: null
		},
		{
			key: 'pro',
			name: 'Fiscal',
			description: 'Pour les gestionnaires patrimoniaux exigeants',
			monthlyPrice: 39,
			yearlyPrice: 348,
			popular: true,
			features: [
				'SCI illimitées',
				'Biens illimités',
				'Calcul de rentabilité avancé',
				'Dashboard complet multi-SCI',
				'Résumé fiscal PDF (CERFA 2044)',
				'Tout Gestion inclus',
				'Support prioritaire dédié'
			],
			cta: 'Choisir Fiscal',
			href: null
		}
	];

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

	const faqItems = [
		{
			question: 'Le produit est-il adapté à une petite SCI familiale ?',
			answer:
				"Absolument. L'interface est pensée pour démarrer simple avec 1-2 biens, puis monter en sophistication sans refonte."
		},
		{
			question: 'Puis-je l\'utiliser avec mon expert-comptable actuel ?',
			answer:
				'Oui. Les données sont structurées pour faciliter les échanges avec votre comptable. Un résumé fiscal PDF par exercice est disponible sur le plan Fiscal.'
		},
		{
			question: 'Mes données sont-elles sécurisées (RGPD) ?',
			answer:
				'Oui. Hébergement UE via Supabase, isolation des données par SCI et espace confidentialité dédié (résumé des données, export JSON, suppression de compte).'
		},
		{
			question: 'Comment migrer depuis Excel ou autre outil ?',
			answer:
				'La version actuelle privilégie une saisie structurée rapide pour repartir sur des bases fiables. Un module d\'import CSV/Excel est prévu dans la roadmap.'
		},
		{
			question: "L'outil gère-t-il la conformité fiscale (2044, 2072) ?",
			answer:
				'Un calcul simplifié du résultat foncier (revenus − charges) est disponible avec export PDF. Le CERFA 2072 (SCI à l\'IS) est prévu dans une version future.'
		},
		{
			question: 'Que se passe-t-il si je veux arrêter ?',
			answer:
				'Aucun engagement. Vous pouvez arrêter votre abonnement Stripe à tout moment et demander la suppression de votre compte depuis l\'espace confidentialité.'
		}
	];

	const colorMap: Record<string, { bg: string; text: string }> = {
		emerald: {
			bg: 'bg-emerald-100 dark:bg-emerald-900/30',
			text: 'text-emerald-600 dark:text-emerald-400'
		},
		blue: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-600 dark:text-blue-400' },
		cyan: { bg: 'bg-cyan-100 dark:bg-cyan-900/30', text: 'text-cyan-600 dark:text-cyan-400' },
		amber: {
			bg: 'bg-amber-100 dark:bg-amber-900/30',
			text: 'text-amber-600 dark:text-amber-400'
		},
		violet: {
			bg: 'bg-violet-100 dark:bg-violet-900/30',
			text: 'text-violet-600 dark:text-violet-400'
		},
		rose: { bg: 'bg-rose-100 dark:bg-rose-900/30', text: 'text-rose-600 dark:text-rose-400' }
	};

	function formatPrice(plan: (typeof plans)[0]): string {
		if (plan.monthlyPrice === 0) return 'Gratuit';
		if (billingPeriod === 'month') return `${plan.monthlyPrice}€`;
		return `${plan.yearlyPrice}€`;
	}

	function formatPeriod(plan: (typeof plans)[0]): string {
		if (plan.monthlyPrice === 0) return '';
		if (billingPeriod === 'month') return '/mois';
		return '/an';
	}

	function formatPriceTTC(plan: (typeof plans)[0]): string | null {
		if (plan.monthlyPrice === 0) return null;
		const ht = billingPeriod === 'month' ? plan.monthlyPrice : plan.yearlyPrice;
		const ttc = (ht * 1.2).toFixed(2).replace('.', ',');
		const period = billingPeriod === 'month' ? '/mois' : '/an';
		return `(${ttc}\u202F\u20AC TTC${period})`;
	}
</script>

<svelte:head>
	<title>GererSCI — Gestion simplifiée de vos SCI</title>
	<meta
		name="description"
		content="Centralisez biens, loyers et documents. Dashboard multi-SCI, quittances PDF, fiscalité CERFA 2044."
	/>
	<link rel="canonical" href="https://gerersci.fr" />
	{@html `<script type="application/ld+json">${JSON.stringify({
		"@context": "https://schema.org",
		"@type": "SoftwareApplication",
		"name": "GererSCI",
		"applicationCategory": "BusinessApplication",
		"operatingSystem": "Web",
		"description": "Gestion simplifiée de Sociétés Civiles Immobilières",
		"url": "https://gerersci.fr",
		"offers": [
			{ "@type": "Offer", "price": "0", "priceCurrency": "EUR", "name": "Essentiel" },
			{ "@type": "Offer", "price": "19", "priceCurrency": "EUR", "name": "Gestion" },
			{ "@type": "Offer", "price": "39", "priceCurrency": "EUR", "name": "Fiscal" }
		]
	})}</script>`}
</svelte:head>

<main class="min-h-screen bg-slate-50 dark:bg-slate-950">
	<!-- ============================================================ -->
	<!-- HERO -->
	<!-- ============================================================ -->
	<section class="relative overflow-hidden bg-white py-20 sm:py-32 dark:bg-slate-900">
		<div
			class="pointer-events-none absolute inset-0 bg-gradient-to-br from-blue-50/80 via-transparent to-cyan-50/60 dark:from-blue-950/30 dark:to-cyan-950/20"
		></div>
		<div class="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="mx-auto max-w-3xl text-center">
				<Badge variant="secondary" class="mb-6 px-3 py-1 text-sm font-medium">
					Produit SaaS pour SCI & immobilier locatif
				</Badge>
				<h1
					class="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl dark:text-white"
				>
					Votre SCI mérite mieux
					<span
						class="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent"
					>
						qu'un tableur Excel
					</span>
				</h1>
				<p class="mt-6 text-lg leading-8 text-slate-600 sm:text-xl dark:text-slate-400">
					Centralisez biens, loyers et documents en un seul endroit. Moins
					d'administratif, plus de visibilité sur vos revenus, retards et la performance de
					chaque bien.
				</p>
				<div class="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
					<a href="#pricing">
						<Button
							size="lg"
							class="bg-blue-600 px-8 text-lg font-semibold text-white hover:bg-blue-700"
						>
							Démarrer à 19€/mois
							<ArrowRight class="ml-2 h-5 w-5" />
						</Button>
					</a>
					<a href="/register">
						<Button variant="outline" size="lg" class="px-8 text-lg font-semibold">
							Essayer gratuitement
						</Button>
					</a>
				</div>
			</div>

			<!-- Trust bar -->
			<div class="mt-10 flex flex-wrap items-center justify-center gap-4 text-sm text-slate-500 dark:text-slate-400">
				<span>Hébergé en UE</span>
				<span class="text-slate-300 dark:text-slate-600">·</span>
				<span>RGPD</span>
				<span class="text-slate-300 dark:text-slate-600">·</span>
				<span>Sans engagement</span>
				<span class="text-slate-300 dark:text-slate-600">·</span>
				<span>Annulez à tout moment</span>
			</div>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- HERO SCREENSHOT -->
	<!-- ============================================================ -->
	<section class="py-16 bg-white dark:bg-slate-950">
		<div class="mx-auto max-w-6xl px-6">
			<div class="relative mx-auto">
				<!-- Browser frame -->
				<div class="rounded-xl border border-slate-200 dark:border-slate-700 shadow-2xl overflow-hidden">
					<!-- Browser bar -->
					<div class="flex items-center gap-2 px-4 py-3 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
						<div class="flex gap-1.5">
							<div class="w-3 h-3 rounded-full bg-red-400"></div>
							<div class="w-3 h-3 rounded-full bg-amber-400"></div>
							<div class="w-3 h-3 rounded-full bg-emerald-400"></div>
						</div>
						<div class="flex-1 mx-4">
							<div class="bg-white dark:bg-slate-700 rounded-md px-3 py-1 text-xs text-slate-400 text-center">
								gerersci.fr/dashboard
							</div>
						</div>
					</div>
					<!-- Screenshot -->
					<button onclick={() => openLightbox(0)} class="block w-full cursor-zoom-in">
						<img
							src="/images/showcase/dashboard-light.png"
							alt="Dashboard GererSCI — 2 SCI, 4 biens, 100% recouvrement, 64 900EUR cashflow"
							class="w-full block dark:hidden"
							fetchpriority="high"
							decoding="async"
							width="1440"
							height="900"
						/>
						<img
							src="/images/showcase/dashboard-dark.png"
							alt="Dashboard GererSCI en mode sombre"
							class="w-full hidden dark:block"
							fetchpriority="high"
							decoding="async"
							width="1440"
							height="900"
						/>
					</button>
				</div>
			</div>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- FEATURE SECTIONS -->
	<!-- ============================================================ -->
	{#each featureSections as feature, i}
		<section class="py-16 {i % 2 === 0 ? 'bg-slate-50 dark:bg-slate-900/50' : 'bg-white dark:bg-slate-950'}">
			<div class="mx-auto max-w-6xl px-6">
				<div class="grid lg:grid-cols-2 gap-12 items-center {i % 2 !== 0 ? 'lg:grid-flow-col-dense' : ''}">
					<!-- Image -->
					<div class="{i % 2 !== 0 ? 'lg:col-start-2' : ''}">
						<button onclick={() => openLightbox(i + 1)} class="block w-full cursor-zoom-in group">
							<div class="rounded-xl border border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden transition-shadow group-hover:shadow-2xl">
								<!-- Browser bar mini -->
								<div class="flex items-center gap-1.5 px-3 py-2 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
									<div class="w-2 h-2 rounded-full bg-red-400"></div>
									<div class="w-2 h-2 rounded-full bg-amber-400"></div>
									<div class="w-2 h-2 rounded-full bg-emerald-400"></div>
								</div>
								<img
									src={feature.image}
									alt={feature.alt}
									class="w-full"
									loading="lazy"
									decoding="async"
									width="1440"
									height="900"
								/>
							</div>
						</button>
					</div>
					<!-- Text -->
					<div class="{i % 2 !== 0 ? 'lg:col-start-1' : ''}">
						<span class="text-sm font-semibold text-sky-600 dark:text-sky-400">{feature.eyebrow}</span>
						<h3 class="mt-2 text-2xl font-bold text-slate-900 dark:text-slate-100">{feature.title}</h3>
						<p class="mt-3 text-slate-600 dark:text-slate-400 leading-relaxed">{feature.description}</p>
						<ul class="mt-4 space-y-2">
							{#each feature.bullets as bullet}
								<li class="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
									<Check class="h-4 w-4 flex-shrink-0 text-emerald-500" />
									{bullet}
								</li>
							{/each}
						</ul>
					</div>
				</div>
			</div>
		</section>
	{/each}

	<!-- ============================================================ -->
	<!-- TARGET AUDIENCE -->
	<!-- ============================================================ -->
	<section class="bg-white py-20 dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="mb-12 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium"
					>Pour qui ?</Badge
				>
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

	<!-- ============================================================ -->
	<!-- FEATURES -->
	<!-- ============================================================ -->
	<section id="features" class="bg-slate-50 py-20 dark:bg-slate-950">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="mb-16 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium"
					>Fonctionnalités</Badge
				>
				<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
					Tout ce dont vous avez besoin pour gérer vos SCI
				</h2>
				<p class="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
					Des outils concrets pour gagner du temps, réduire les erreurs et prendre de meilleures
					décisions.
				</p>
			</div>

			<div class="grid gap-8 md:grid-cols-2">
				{#each features as feature}
					{@const colors = colorMap[feature.color] ?? colorMap.blue}
					<article
						class="rounded-2xl border border-slate-200 bg-white p-6 transition-shadow hover:shadow-lg dark:border-slate-700 dark:bg-slate-800"
					>
						<div
							class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl {colors.bg}"
						>
							<feature.icon class="h-6 w-6 {colors.text}" />
						</div>
						<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
							{feature.title}
						</h3>
						<p class="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
							{feature.description}
						</p>
					</article>
				{/each}
			</div>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- PRICING -->
	<!-- ============================================================ -->
	<section id="pricing" class="bg-white py-20 dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="mb-12 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Tarifs</Badge>
				<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
					Un prix simple, sans surprise
				</h2>
				<p class="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
					Commencez gratuitement, passez au plan supérieur quand vous en avez besoin.
				</p>

				<!-- Billing toggle -->
				<div class="mt-8 inline-flex items-center rounded-xl bg-slate-100 p-1 shadow-sm dark:bg-slate-800">
					<button
						class="rounded-lg px-5 py-2 text-sm font-medium transition-colors {billingPeriod === 'month'
							? 'bg-blue-600 text-white shadow-sm'
							: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
						onclick={() => (billingPeriod = 'month')}
					>
						Mensuel
					</button>
					<button
						class="rounded-lg px-5 py-2 text-sm font-medium transition-colors {billingPeriod === 'year'
							? 'bg-blue-600 text-white shadow-sm'
							: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
						onclick={() => (billingPeriod = 'year')}
					>
						Annuel
						<span class="ml-1 text-xs font-normal opacity-80">-2 mois</span>
					</button>
				</div>
			</div>

			<div class="grid gap-8 md:grid-cols-3">
				{#each plans as plan}
					<div
						class="relative flex flex-col rounded-2xl border bg-white p-8 transition-shadow hover:shadow-lg dark:bg-slate-800 {plan.popular
							? 'border-blue-500 shadow-lg shadow-blue-500/10 dark:border-blue-400'
							: 'border-slate-200 dark:border-slate-700'}"
					>
						{#if plan.popular}
							<div class="absolute -top-3 left-1/2 -translate-x-1/2">
								<Badge
									class="bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-600"
								>
									Populaire
								</Badge>
							</div>
						{/if}

						<div class="mb-6">
							<h3 class="text-xl font-bold text-slate-900 dark:text-slate-100">
								{plan.name}
							</h3>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								{plan.description}
							</p>
						</div>

						<div class="mb-6">
							<span class="text-4xl font-extrabold text-slate-900 dark:text-white">
								{formatPrice(plan)}
							</span>
							{#if plan.monthlyPrice > 0}
								<span class="text-slate-500 dark:text-slate-400">
									HT{formatPeriod(plan)}
								</span>
								<div class="mt-1 text-sm text-slate-400 dark:text-slate-500">
									{formatPriceTTC(plan)}
								</div>
								{#if billingPeriod === 'year'}
									<div class="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
										Économisez 2 mois par rapport au mensuel
									</div>
								{/if}
							{/if}
						</div>

						<ul class="mb-8 flex-1 space-y-3">
							{#each plan.features as feat}
								<li class="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-400">
									<Check
										class="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600 dark:text-blue-400"
									/>
									<span>{feat}</span>
								</li>
							{/each}
						</ul>

						{#if plan.href}
							<a href={plan.href} class="mt-auto">
								<Button
									class="w-full {plan.popular
										? 'bg-blue-600 text-white hover:bg-blue-700'
										: ''}"
									variant={plan.popular ? 'default' : 'outline'}
									size="lg"
								>
									{plan.cta}
								</Button>
							</a>
						{:else}
							<Button
								class="mt-auto w-full {plan.popular
									? 'bg-blue-600 text-white hover:bg-blue-700'
									: ''}"
								variant={plan.popular ? 'default' : 'outline'}
								size="lg"
								disabled={checkoutLoading === plan.key}
								onclick={() => createGuestCheckout(plan.key)}
							>
								{#if checkoutLoading === plan.key}
									<Loader2 class="mr-2 h-4 w-4 animate-spin" />
									Redirection...
								{:else}
									{plan.cta}
								{/if}
							</Button>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- MARKET DATA -->
	<!-- ============================================================ -->
	<section id="market-data" class="bg-slate-50 py-20 dark:bg-slate-950">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="mb-16 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium"
					>Données du secteur</Badge
				>
				<h2 class="mb-4 text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
					Chiffres clés de la gestion immobilière en France
				</h2>
				<p class="mx-auto max-w-2xl text-lg text-slate-600 dark:text-slate-400">
					Sources officielles et études récentes (2024-2025)
				</p>
			</div>

			<!-- KPI highlight cards -->
			<div class="mb-16 grid gap-6 md:grid-cols-3">
				<div class="rounded-2xl bg-white p-8 text-center dark:bg-slate-800">
					<TrendingUp class="mx-auto mb-3 h-8 w-8 text-blue-600 dark:text-blue-400" />
					<div class="text-3xl font-bold text-slate-900 dark:text-white">3,50%</div>
					<div class="mt-1 text-sm text-slate-600 dark:text-slate-400">
						Taux d'impayés moyen en France (2025)
					</div>
					<div class="mt-2 text-xs text-slate-500">Source: Lamy Immobilier</div>
				</div>
				<div class="rounded-2xl bg-white p-8 text-center dark:bg-slate-800">
					<Calculator class="mx-auto mb-3 h-8 w-8 text-blue-600 dark:text-blue-400" />
					<div class="text-3xl font-bold text-slate-900 dark:text-white">50%</div>
					<div class="mt-1 text-sm text-slate-600 dark:text-slate-400">
						du temps libérable par l'automatisation
					</div>
					<div class="mt-2 text-xs text-slate-500">Source: McKinsey / Euodia</div>
				</div>
				<div class="rounded-2xl bg-white p-8 text-center dark:bg-slate-800">
					<Shield class="mx-auto mb-3 h-8 w-8 text-blue-600 dark:text-blue-400" />
					<div class="text-3xl font-bold text-slate-900 dark:text-white">72%</div>
					<div class="mt-1 text-sm text-slate-600 dark:text-slate-400">
						constatent une amélioration en 12 mois
					</div>
					<div class="mt-2 text-xs text-slate-500">Source: Deloitte / Septeo</div>
				</div>
			</div>

			<!-- KPI Section -->
			<div class="mb-16 rounded-2xl bg-white p-8 dark:bg-slate-800">
				<h3 class="mb-8 text-center text-2xl font-bold text-slate-900 dark:text-slate-100">
					KPI critiques à suivre (standards sectoriels)
				</h3>
				<div class="grid gap-6 md:grid-cols-3">
					<div class="text-center">
						<div class="mb-2 text-4xl font-bold text-blue-600 dark:text-blue-400">&gt;98%</div>
						<div class="text-slate-600 dark:text-slate-400">Taux de recouvrement optimal</div>
						<div class="mt-1 text-sm text-slate-500">Source: Lockimmo</div>
					</div>
					<div class="text-center">
						<div class="mb-2 text-4xl font-bold text-blue-600 dark:text-blue-400">5%</div>
						<div class="text-slate-600 dark:text-slate-400">Taux de vacance cible</div>
						<div class="mt-1 text-sm text-slate-500">Source: CAFPI</div>
					</div>
					<div class="text-center">
						<div class="mb-2 text-4xl font-bold text-blue-600 dark:text-blue-400">30j</div>
						<div class="text-slate-600 dark:text-slate-400">Délai de paiement légal</div>
						<div class="mt-1 text-sm text-slate-500">Source: Manda</div>
					</div>
				</div>
			</div>

			<!-- Studies Section -->
			<div id="studies" class="rounded-2xl bg-white p-8 dark:bg-slate-800">
				<div class="mb-8 text-center">
					<div
						class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30"
					>
						<FileText class="h-6 w-6 text-blue-600 dark:text-blue-400" />
					</div>
					<h3 class="mb-2 text-2xl font-bold text-slate-900 dark:text-slate-100">
						Études détaillées consultées
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Synthèse issue des études documentées.
					</p>
				</div>

				<div class="grid gap-4 md:grid-cols-2">
					{#each studyReferences as study (study.title)}
						<article
							class="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/60"
						>
							<h4 class="mb-2 text-lg font-semibold text-slate-900 dark:text-slate-100">
								{study.title}
							</h4>
							<p class="mb-3 text-sm text-slate-600 dark:text-slate-400">{study.finding}</p>
							<a
								href={study.url}
								target="_blank"
								rel="noopener noreferrer"
								class="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
							>
								Source: {study.source}
							</a>
						</article>
					{/each}
				</div>
			</div>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- FAQ -->
	<!-- ============================================================ -->
	<section class="bg-white py-20 dark:bg-slate-900">
		<div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
			<div class="mb-12 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium"
					>Questions fréquentes</Badge
				>
				<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
					Tout ce que vous devez savoir
				</h2>
			</div>

			<div class="space-y-3">
				{#each faqItems as item, i}
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800"
					>
						<button
							class="flex w-full items-center justify-between rounded-2xl px-6 py-5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
							aria-expanded={openFaqIndex === i}
							onclick={() => (openFaqIndex = openFaqIndex === i ? null : i)}
						>
							<span class="pr-4 text-base font-semibold text-slate-900 dark:text-slate-100">
								{item.question}
							</span>
							{#if openFaqIndex === i}
								<ChevronUp
									class="h-5 w-5 flex-shrink-0 text-slate-400 dark:text-slate-500"
								/>
							{:else}
								<ChevronDown
									class="h-5 w-5 flex-shrink-0 text-slate-400 dark:text-slate-500"
								/>
							{/if}
						</button>
						{#if openFaqIndex === i}
							<div class="px-6 pb-5 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
								{item.answer}
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- FINAL CTA -->
	<!-- ============================================================ -->
	<section class="bg-gradient-to-r from-blue-600 to-cyan-600 py-20">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center">
				<h2 class="mb-4 text-3xl font-bold text-white sm:text-4xl">
					Créez votre compte gratuitement
				</h2>
				<p class="mx-auto mb-8 max-w-2xl text-lg text-blue-100">
					Sans engagement. Annulez quand vous voulez.
				</p>
				<div class="flex flex-col items-center justify-center gap-4 sm:flex-row">
					<a href="/register">
						<Button
							size="lg"
							class="bg-white px-8 text-lg font-semibold text-blue-600 shadow-lg hover:bg-blue-50"
						>
							Commencer gratuitement
							<ArrowRight class="ml-2 h-5 w-5" />
						</Button>
					</a>
					<a href="#pricing">
						<Button
							variant="outline"
							size="lg"
							class="border-white/30 px-8 text-lg font-semibold text-white hover:bg-white/10"
						>
							Comparer les plans
						</Button>
					</a>
				</div>
			</div>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- LIGHTBOX GALLERY -->
	<!-- ============================================================ -->
	{#if lightboxOpen}
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
		<div
			class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
			onclick={closeLightbox}
			onkeydown={(e) => {
				if (e.key === 'Escape') closeLightbox();
				if (e.key === 'ArrowRight') nextImage();
				if (e.key === 'ArrowLeft') prevImage();
			}}
			role="dialog"
			aria-modal="true"
			aria-label="Galerie d'images"
			tabindex="-1"
		>
			<!-- Close button -->
			<button onclick={closeLightbox} class="absolute top-6 right-6 text-white/80 hover:text-white z-10" aria-label="Fermer">
				<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
			</button>

			<!-- Previous -->
			<button onclick={(e) => { e.stopPropagation(); prevImage(); }} class="absolute left-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-2" aria-label="Image precedente">
				<svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
			</button>

			<!-- Image -->
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div onclick={(e) => e.stopPropagation()} class="max-w-[90vw] max-h-[85vh]">
				<img
					src={allImages[lightboxIndex].src}
					alt={allImages[lightboxIndex].title}
					class="max-w-full max-h-[80vh] rounded-lg shadow-2xl"
				/>
				<div class="mt-3 text-center">
					<p class="text-white/90 font-medium">{allImages[lightboxIndex].title}</p>
					<p class="text-white/50 text-sm">{lightboxIndex + 1} / {allImages.length}</p>
				</div>
			</div>

			<!-- Next -->
			<button onclick={(e) => { e.stopPropagation(); nextImage(); }} class="absolute right-4 top-1/2 -translate-y-1/2 text-white/70 hover:text-white p-2" aria-label="Image suivante">
				<svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
			</button>
		</div>
	{/if}
</main>
