<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getCurrentSession } from '$lib/auth/session';
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
		Loader2,
		Crown
	} from 'lucide-svelte';
	import { API_URL } from '$lib/api';
	import { supabase } from '$lib/supabase';
	import CheckoutConfirmModal from '$lib/components/CheckoutConfirmModal.svelte';
	import AppDemoVideo from '$lib/components/AppDemoVideo.svelte';
	import { trackEvent, EVENTS } from '$lib/analytics';

	onMount(async () => {
		const session = await getCurrentSession();
		if (session?.user) {
			goto('/dashboard');
		}
	});

	let billingPeriod = $state<'month' | 'year'>('month');
	let checkoutLoading = $state<string | null>(null);
	let modalOpen = $state(false);
	let modalPlanKey = $state('');
	let modalPlanName = $state('');
	let modalPlanPrice = $state('');
	let modalPlanPeriod = $state('');
	let modalPlanFeatures = $state<string[]>([]);
	let openFaqIndex = $state<number | null>(null);

	// Demo video scene sync
	let demoScene = $state(0);
	// Lightbox state
	let lightboxOpen = $state(false);
	let lightboxIndex = $state(0);

	const allImages = [
		{ src: '/images/showcase/dashboard-light.png', title: 'Tableau de bord' },
		{ src: '/images/showcase/biens-grid.png', title: 'Grille des biens' },
		{ src: '/images/showcase/loyers-with-button.png', title: 'Suivi des loyers' },
		{ src: '/images/showcase/fiche-identite.png', title: 'Associés' },
		{ src: '/images/showcase/finances-consolidated.png', title: 'Vue financière' },
		{ src: '/images/showcase/onboarding-step1.png', title: 'Onboarding' },
	];

	function openLightbox(index: number) {
		trackEvent(EVENTS.LANDING_LIGHTBOX_OPEN, { image: index });
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

	async function openCheckoutModal(planKey: string) {
		trackEvent(EVENTS.LANDING_PLAN_SELECT, { plan: planKey });

		// Anonymous → redirect to register
		const { data: { session } } = await supabase.auth.getSession();
		if (!session) {
			goto(`/register?plan=${planKey}`);
			return;
		}

		const plan = plans.find((p: any) => p.key === planKey);
		if (!plan) return;
		modalPlanKey = planKey;
		modalPlanName = plan.name;
		modalPlanPrice = billingPeriod === 'month' ? `${plan.monthlyPrice}€` : `${plan.yearlyPrice}€`;
		modalPlanPeriod = billingPeriod === 'month' ? '/mois' : '/an';
		modalPlanFeatures = plan.features;
		modalOpen = true;
	}

	function handleModalConfirm() {
		modalOpen = false;
		createGuestCheckout(modalPlanKey);
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
			key: 'starter',
			name: 'Gestion',
			description: 'Automatisez votre gestion locative',
			monthlyPrice: 19,
			yearlyPrice: 190,
			popular: false,
			features: [
				'1 SCI',
				'5 biens',
				'Quittances PDF conformes',
				'Suivi des loyers + relances auto',
				'Résumé fiscal CERFA 2044',
				'Charges, PNO, frais agence',
				'Export CSV',
				'Support email 48h'
			],
			cta: 'Démarrer pour 19€/mois',
			href: null
		},
		{
			key: 'pro',
			name: 'Pilotage',
			description: 'Votre co-pilote fiscal et juridique',
			monthlyPrice: 39,
			yearlyPrice: 390,
			popular: true,
			features: [
				'SCI illimitées',
				'Biens illimités',
				'Tout Gestion inclus',
				'Assemblées générales + convocations',
				'Mouvements de parts + simulation droits',
				'Moteur 44+ échéances',
				'Calendrier fiscal interactif',
				'Vue comptable annuelle',
				'Révision IRL automatique',
				'Support prioritaire 24h'
			],
			cta: 'Démarrer pour 39€/mois',
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

	const valueStack = [
		{ item: 'Gestion locative complète', value: '25€/mois' },
		{ item: 'Quittances PDF conformes', value: '10€/mois' },
		{ item: 'Module fiscal CERFA 2044', value: '80€/mois' },
		{ item: 'Suivi charges et PNO', value: '20€/mois' },
		{ item: 'Calcul de rentabilité', value: '50€/mois' },
		{ item: 'Registre AG + convocations', value: '40€/mois' },
		{ item: 'Mouvements de parts', value: '30€/mois' },
		{ item: 'Calendrier fiscal + échéances', value: '17€/mois' },
		{ item: 'Notifications intelligentes', value: '10€/mois' },
		{ item: 'Tableau de bord multi-SCI', value: '30€/mois' },
		{ item: 'Import/Export données', value: '15€/mois' }
	];

	const faqItems = [
		{
			question: 'Mon comptable s\'occupe déjà de tout',
			answer:
				"Votre comptable intervient en fin d'année pour la déclaration. GérerSCI vous aide au quotidien : suivi des loyers, relances automatiques, quittances, charges. Vous arrivez chez votre comptable avec des données propres et structurées — il vous en remerciera."
		},
		{
			question: '19€/mois c\'est trop cher',
			answer:
				"Un retard de loyer non détecté vous coûte 800€ minimum. Une erreur sur la 2044 peut déclencher un contrôle fiscal. GérerSCI remplace en moyenne 150€/mois de prestations (quittances, suivi comptable, gestion locative). C'est 6x moins cher que le minimum."
		},
		{
			question: 'J\'ai seulement 1 bien',
			answer:
				"Le plan Gestion à 19€/mois est conçu pour vous. Un seul bien mal géré peut coûter des milliers d'euros en impayés ou en erreurs fiscales. Et quand vous ajouterez un deuxième bien, tout sera déjà en place."
		},
		{
			question: 'Mes données sont-elles sécurisées ?',
			answer:
				'Hébergement UE via Supabase (PostgreSQL), isolation des données par SCI avec Row-Level Security, chiffrement en transit et au repos. Espace confidentialité dédié avec export JSON et suppression de compte. Conforme RGPD.'
		},
		{
			question: 'Je peux faire ça avec Excel',
			answer:
				"Vous pouvez. Mais Excel ne génère pas de quittances PDF conformes, ne calcule pas votre CERFA 2044, ne vous alerte pas sur un loyer en retard, et ne produit pas de calendrier fiscal. GérerSCI fait tout ça en 10 minutes par mois."
		},
		{
			question: 'Et si je veux annuler ?',
			answer:
				'Annulation en 1 clic depuis votre espace. Pas de période d\'engagement, pas de frais cachés. Vos données restent accessibles 30 jours après annulation. Garantie satisfait ou remboursé 30 jours.'
		},
		{
			question: 'Je ne suis pas à l\'aise avec l\'informatique',
			answer:
				"L'onboarding guidé vous accompagne pas à pas : créer votre SCI, ajouter un bien, configurer un bail. En 5 minutes, vous êtes opérationnel. Et le support répond sous 48h (24h en Pilotage)."
		},
		{
			question: 'C\'est un nouveau produit',
			answer:
				"GérerSCI est développé par des gérants de SCI, pour des gérants de SCI. Le produit est en production, utilisé quotidiennement. L'offre Fondateur vous donne un accès à vie au meilleur prix — et un accès beta à toutes les nouvelles fonctionnalités."
		},
		{
			question: 'Est-ce que ça remplace la déclaration fiscale ?',
			answer:
				"Non. GérerSCI prépare vos données fiscales : résumé CERFA 2044, résultat foncier, répartition par associé. Votre comptable ou vous-même restez responsable de la déclaration finale. Les calculs sont fournis à titre indicatif."
		},
		{
			question: 'Pourquoi pas d\'offre gratuite ?',
			answer:
				"Un outil gratuit ne peut pas offrir un support de qualité, des mises à jour régulières et la sécurité que vos données méritent. Le plan Gestion à 19€/mois vous donne un outil professionnel complet. Garantie 30 jours satisfait ou remboursé — si l'outil ne vous convient pas, on vous rembourse sans condition."
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
		if (billingPeriod === 'month') return `${plan.monthlyPrice}€`;
		return `${plan.yearlyPrice}€`;
	}

	function formatPeriod(): string {
		if (billingPeriod === 'month') return '/mois';
		return '/an';
	}

	function formatPriceTTC(plan: (typeof plans)[0]): string {
		const ht = billingPeriod === 'month' ? plan.monthlyPrice : plan.yearlyPrice;
		const ttc = (ht * 1.2).toFixed(2).replace('.', ',');
		const period = billingPeriod === 'month' ? '/mois' : '/an';
		return `(${ttc} € TTC${period})`;
	}
</script>

<svelte:window onkeydown={(e) => {
	if (!lightboxOpen) return;
	if (e.key === 'Escape') closeLightbox();
	if (e.key === 'ArrowRight') nextImage();
	if (e.key === 'ArrowLeft') prevImage();
}} />

<svelte:head>
	<title>GérerSCI — Gestion simplifiée de vos SCI</title>
	<meta
		name="description"
		content="Gérez vos biens, vos locataires et votre fiscalité depuis un seul tableau de bord — en 10 minutes par mois."
	/>
	<link rel="canonical" href="https://gerersci.fr" />
	{@html `<script type="application/ld+json">${JSON.stringify({
		"@context": "https://schema.org",
		"@type": "SoftwareApplication",
		"name": "GérerSCI",
		"applicationCategory": "BusinessApplication",
		"operatingSystem": "Web",
		"description": "Gestion simplifiée de Sociétés Civiles Immobilières",
		"url": "https://gerersci.fr",
		"offers": [
			{ "@type": "Offer", "price": "19", "priceCurrency": "EUR", "name": "Gestion" },
			{ "@type": "Offer", "price": "39", "priceCurrency": "EUR", "name": "Pilotage" },
			{ "@type": "Offer", "price": "500", "priceCurrency": "EUR", "name": "Fondateur" }
		]
	})}</script>`}
	{@html `<script type="application/ld+json">${JSON.stringify({
		"@context": "https://schema.org",
		"@type": "FAQPage",
		"mainEntity": faqItems.map(item => ({
			"@type": "Question",
			"name": item.question,
			"acceptedAnswer": { "@type": "Answer", "text": item.answer }
		}))
	})}</script>`}
	<link rel="alternate" hreflang="fr" href="https://gerersci.fr/" />
	<meta property="og:title" content="GérerSCI — Gestion simplifiée de vos SCI" />
	<meta property="og:description" content="Pilotez vos SCI en 10 minutes par mois. Biens, baux, quittances, CERFA 2044, le tout au même endroit." />
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://gerersci.fr" />
	<meta property="og:image" content="https://gerersci.fr/images/showcase/dashboard-light.png" />
	<meta property="og:locale" content="fr_FR" />
	<meta property="og:site_name" content="GérerSCI" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="GérerSCI — Gestion simplifiée de vos SCI" />
	<meta name="twitter:description" content="Pilotez vos SCI en 10 minutes par mois." />
	<meta name="twitter:image" content="https://gerersci.fr/images/showcase/dashboard-light.png" />
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
					Utilisé par des gérants de SCI partout en France
				</Badge>
				<h1
					class="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl dark:text-white"
				>
					Vos loyers encaissés.
					<span
						class="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent"
					>
						Votre fiscalité claire.
					</span>
					Votre SCI sous contrôle.
				</h1>
				<p class="mt-6 text-lg leading-8 text-slate-600 sm:text-xl dark:text-slate-400">
					Tout ce qu'il faut pour piloter votre SCI en 10 minutes par mois — biens, baux, quittances, CERFA 2044, le tout au même endroit.
				</p>
				<div class="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
					<Button
						size="lg"
						class="bg-blue-600 px-8 text-lg font-semibold text-white hover:bg-blue-700"
						onclick={() => { trackEvent(EVENTS.LANDING_CTA_CLICK, { cta: 'comment_ca_marche' }); document.getElementById('comment-ca-marche')?.scrollIntoView({ behavior: 'smooth' }); }}
					>
						Voir comment ça marche
						<ArrowRight class="ml-2 h-5 w-5" />
					</Button>
					<Button
						size="lg"
						variant="outline"
						class="px-8 text-lg font-semibold"
						onclick={() => { trackEvent(EVENTS.LANDING_CTA_CLICK, { cta: 'comparer_plans' }); document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' }); }}
					>
						Comparer les plans
					</Button>
				</div>
			</div>

			<!-- Trust bar -->
			<div class="mt-10 flex flex-wrap items-center justify-center gap-4 text-sm text-slate-500 dark:text-slate-400">
				<span>🇫🇷 Hébergé en France</span>
				<span class="text-slate-300 dark:text-slate-600">·</span>
				<span>🔒 Conforme RGPD</span>
				<span class="text-slate-300 dark:text-slate-600">·</span>
				<span>💶 Satisfait ou remboursé 30j</span>
			</div>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- COMMENT ÇA MARCHE + DEMO VIDEO (merged) -->
	<!-- ============================================================ -->
	<section id="comment-ca-marche" class="bg-white py-20 dark:bg-slate-900">
		<div class="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
			<div class="mb-12 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Simple</Badge>
				<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
					Comment ça marche — en 3 étapes
				</h2>
			</div>

			<!-- Demo video -->
			<div class="mx-auto max-w-5xl">
				<AppDemoVideo activeScene={demoScene} onSceneChange={(i) => { demoScene = i; }} />
			</div>

			<!-- Step navigation cards -->
			<div class="mt-8 grid gap-4 md:grid-cols-3">
				{#each [
					{ step: '①', title: 'Créez votre SCI', time: '2 minutes', desc: "Nom, régime fiscal, c'est tout.", sceneStart: 0, sceneEnd: 0 },
					{ step: '②', title: 'Ajoutez vos biens', time: '5 minutes', desc: 'Biens, loyers, associés — on vous guide.', sceneStart: 1, sceneEnd: 3 },
					{ step: '③', title: 'Pilotez chaque mois', time: '10 min/mois', desc: 'Finances, KPIs, alertes — automatisé.', sceneStart: 4, sceneEnd: 5 }
				] as card, i}
					{@const isActive = demoScene >= card.sceneStart && demoScene <= card.sceneEnd}
					<button
						class="rounded-xl border p-4 text-left transition-all duration-200 {isActive
							? 'border-blue-500 bg-blue-50 shadow-md dark:border-blue-400 dark:bg-blue-950/30'
							: 'border-slate-200 bg-slate-50 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600'}"
						onclick={() => { demoScene = card.sceneStart; trackEvent(EVENTS.LANDING_STEP_MODAL_OPEN, { step: i + 1 }); }}
					>
						<div class="flex items-center gap-3">
							<span class="flex h-9 w-9 items-center justify-center rounded-full text-base font-bold {isActive ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-400'}">{card.step}</span>
							<div>
								<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">{card.title}</p>
								<p class="text-xs text-slate-500 dark:text-slate-400">{card.time} · {card.desc}</p>
							</div>
						</div>
					</button>
				{/each}
			</div>
		</div>
	</section>

	<!-- Lead magnet links (moved from removed feature sections) -->
	<section class="bg-slate-50 py-8 dark:bg-slate-900/50">
		<div class="mx-auto flex max-w-4xl flex-wrap items-center justify-center gap-6 px-6">
			<a href="/simulateur-cerfa" class="inline-flex items-center gap-2 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300">
				Essayer le simulateur CERFA 2044 gratuit →
			</a>
			<a href="/generateur-quittance" class="inline-flex items-center gap-2 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300">
				Générer une quittance gratuitement →
			</a>
		</div>
	</section>

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
						class="rounded-2xl border border-slate-200 bg-white p-6 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 hover:border-sky-200 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-sky-700"
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
	<!-- VALUE STACK -->
	<!-- ============================================================ -->
	<section class="bg-white py-20 dark:bg-slate-900">
		<div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
			<div class="mb-12 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Valeur</Badge>
				<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
					Tout ce que vous recevez
				</h2>
				<p class="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
					Chaque module remplace un outil ou un prestataire que vous payez déjà.
				</p>
			</div>

			<div class="overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-700">
				<table class="w-full">
					<thead>
						<tr class="bg-slate-50 dark:bg-slate-800">
							<th class="px-6 py-4 text-left text-sm font-semibold text-slate-900 dark:text-slate-100">Ce que vous recevez</th>
							<th class="px-6 py-4 text-right text-sm font-semibold text-slate-900 dark:text-slate-100">Valeur équivalente</th>
						</tr>
					</thead>
					<tbody>
						{#each valueStack as row, i}
							<tr class="{i % 2 === 0 ? 'bg-white dark:bg-slate-900' : 'bg-slate-50/50 dark:bg-slate-800/50'}">
								<td class="px-6 py-3 text-sm text-slate-600 dark:text-slate-400">
									<span class="flex items-center gap-2">
										<Check class="h-4 w-4 flex-shrink-0 text-emerald-500" />
										{row.item}
									</span>
								</td>
								<td class="px-6 py-3 text-right text-sm text-slate-500 line-through dark:text-slate-400">{row.value}</td>
							</tr>
						{/each}
					</tbody>
					<tfoot>
						<tr class="border-t-2 border-slate-300 bg-slate-50 dark:border-slate-600 dark:bg-slate-800">
							<td class="px-6 py-4 text-sm font-bold text-slate-900 dark:text-slate-100">Total</td>
							<td class="px-6 py-4 text-right text-lg font-bold text-slate-400 line-through dark:text-slate-500">327€/mois</td>
						</tr>
						<tr class="bg-blue-50 dark:bg-blue-950/30">
							<td class="px-6 py-4 text-sm font-bold text-blue-700 dark:text-blue-300">Votre prix avec GérerSCI</td>
							<td class="px-6 py-4 text-right text-2xl font-extrabold text-blue-600 dark:text-blue-400">19€/mois</td>
						</tr>
					</tfoot>
				</table>
			</div>

			<p class="mt-6 text-center text-sm leading-relaxed text-slate-600 dark:text-slate-400">
				Vous payeriez plus de 320€ par mois pour assembler tous ces services séparément. Avec GérerSCI, vous avez tout — pour 19€ par mois.
			</p>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- PRICING -->
	<!-- ============================================================ -->
	<section id="pricing" class="bg-slate-50 py-20 dark:bg-slate-950">
		<div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
			<div class="mb-12 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Tarifs</Badge>
				<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
					Un prix simple, sans surprise
				</h2>
				<p class="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
					Chaque SCI mérite un co-pilote. Choisissez le vôtre.
				</p>

				<!-- Billing toggle -->
				<div class="mt-8 inline-flex items-center rounded-xl bg-white p-1 shadow-sm dark:bg-slate-800">
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
						<span class="ml-1 text-xs font-normal opacity-80">2 mois offerts</span>
					</button>
				</div>
			</div>

			<div class="grid gap-8 md:grid-cols-2">
				{#each plans as plan}
					<div
						class="relative flex flex-col rounded-2xl border bg-white p-8 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 dark:bg-slate-800 {plan.popular
							? 'border-blue-500 shadow-lg shadow-blue-500/10 dark:border-blue-400 hover:shadow-blue-500/20'
							: 'border-slate-200 dark:border-slate-700 hover:border-sky-200 dark:hover:border-sky-700'}"
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
							<span class="text-slate-500 dark:text-slate-400">
								HT{formatPeriod()}
							</span>
							<div class="mt-1 text-sm text-slate-400 dark:text-slate-500">
								{formatPriceTTC(plan)}
							</div>
							{#if billingPeriod === 'year'}
								<div class="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
									2 mois offerts
								</div>
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

						<Button
							class="mt-auto w-full {plan.popular
								? 'bg-blue-600 text-white hover:bg-blue-700'
								: ''}"
							variant={plan.popular ? 'default' : 'outline'}
							size="lg"
							disabled={checkoutLoading === plan.key}
							onclick={() => openCheckoutModal(plan.key)}
						>
							{#if checkoutLoading === plan.key}
								<Loader2 class="mr-2 h-4 w-4 animate-spin" />
								Redirection...
							{:else}
								{plan.cta}
							{/if}
						</Button>

						<p class="mt-3 text-center text-xs text-slate-400 dark:text-slate-500">
							Paiement sécurisé · Garanti 30 jours satisfait ou remboursé · Annulation en 1 clic
						</p>
					</div>
				{/each}
			</div>

			<!-- Fondateur offer -->
			<div class="mt-12 rounded-2xl border-2 border-amber-400 bg-gradient-to-br from-amber-50 to-orange-50 p-8 dark:border-amber-500 dark:from-amber-950/30 dark:to-orange-950/30">
				<div class="flex flex-col items-center text-center lg:flex-row lg:text-left lg:items-start lg:gap-8">
					<div class="flex-1">
						<Badge class="mb-3 bg-amber-500 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-500">
							Offre de lancement — 25 places
						</Badge>
						<h3 class="text-2xl font-bold text-slate-900 dark:text-slate-100">
							<Crown class="mr-2 inline h-6 w-6 text-amber-500" />
							Fondateur
						</h3>
						<p class="mt-2 text-slate-600 dark:text-slate-400">
							Accès à vie au plan Pilotage
						</p>
						<ul class="mt-4 space-y-2">
							<li class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
								<Check class="h-4 w-4 flex-shrink-0 text-amber-500" />
								Tout Pilotage inclus — à vie
							</li>
							<li class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
								<Check class="h-4 w-4 flex-shrink-0 text-amber-500" />
								Ligne directe avec le fondateur
							</li>
							<li class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
								<Check class="h-4 w-4 flex-shrink-0 text-amber-500" />
								Accès beta aux nouvelles fonctionnalités
							</li>
						</ul>
					</div>
					<div class="mt-6 flex flex-col items-center lg:mt-0">
						<div class="text-5xl font-extrabold text-slate-900 dark:text-white">500€</div>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							Paiement unique. Pas de mensualité. À vie.
						</p>
						<Button
							size="lg"
							class="mt-4 w-full bg-amber-500 px-8 text-white hover:bg-amber-600"
							disabled={checkoutLoading === 'lifetime'}
							onclick={async () => { const { data: { session } } = await supabase.auth.getSession(); if (!session) { goto('/register?plan=lifetime'); return; } modalPlanKey = 'lifetime'; modalPlanName = 'Fondateur'; modalPlanPrice = '500€'; modalPlanPeriod = ''; modalPlanFeatures = ['Tout Pilotage inclus — à vie', 'Ligne directe avec le fondateur', 'Accès beta aux nouvelles fonctionnalités']; modalOpen = true; }}
						>
							{#if checkoutLoading === 'lifetime'}
								<Loader2 class="mr-2 h-4 w-4 animate-spin" />
								Redirection...
							{:else}
								Devenir Fondateur
							{/if}
						</Button>
						<p class="mt-3 text-sm font-medium text-amber-700 dark:text-amber-400">
							Places restantes sur 25
						</p>
					</div>
				</div>
			</div>

			<p class="mt-10 text-center text-sm text-slate-500 dark:text-slate-400">
				Remplace en moyenne 150€/mois de tableurs, erreurs et temps perdu
			</p>
		</div>
	</section>

	<!-- ============================================================ -->
	<!-- GUARANTEE -->
	<!-- ============================================================ -->
	<section class="bg-white py-16 dark:bg-slate-900">
		<div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
			<div class="rounded-2xl border border-emerald-200 bg-emerald-50 p-8 text-center dark:border-emerald-800 dark:bg-emerald-950/30">
				<Shield class="mx-auto mb-4 h-12 w-12 text-emerald-600 dark:text-emerald-400" />
				<h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100">
					Garantie 30 jours : testez sans risque.
				</h2>
				<p class="mt-4 text-slate-600 dark:text-slate-400">
					30 jours satisfait ou remboursé — sans condition. Si l'outil ne vous convient pas, on vous rembourse.
				</p>
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
							onclick={() => { if (openFaqIndex !== i) trackEvent(EVENTS.LANDING_FAQ_OPEN, { question: i }); openFaqIndex = openFaqIndex === i ? null : i; }}
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
						<div
							class="overflow-hidden px-6 text-sm leading-relaxed text-slate-600 transition-all duration-200 dark:text-slate-400 {openFaqIndex === i ? 'max-h-96 pb-5' : 'max-h-0'}"
						>
							{item.answer}
						</div>
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
					Commencez avec GérerSCI aujourd'hui
				</h2>
				<p class="mx-auto mb-8 max-w-2xl text-lg text-blue-100">
					Carte bancaire requise. Garantie 30 jours satisfait ou remboursé. Annulation en 1 clic.
				</p>
				<div class="flex flex-col items-center justify-center gap-4 sm:flex-row">
					<a href="/pricing">
						<Button
							size="lg"
							class="bg-white px-8 text-lg font-semibold text-blue-600 shadow-lg hover:bg-blue-50"
						>
							Démarrer maintenant
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

	<CheckoutConfirmModal
		open={modalOpen}
		planName={modalPlanName}
		planPrice={modalPlanPrice}
		planPeriod={modalPlanPeriod}
		planFeatures={modalPlanFeatures}
		loading={checkoutLoading !== null}
		onConfirm={handleModalConfirm}
		onCancel={() => { modalOpen = false; }}
	/>

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

