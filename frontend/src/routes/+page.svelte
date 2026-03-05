<svelte:head>
	<title>SCI Manager | Pilotez votre SCI comme un opérateur</title>
	<meta
		name="description"
		content="SCI Manager centralise biens, loyers et documents en un cockpit unique pour accélérer la gestion et sécuriser vos revenus locatifs."
	/>
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<link rel="canonical" href="https://scimanager.fr" />
</svelte:head>

<script>
	import HeroSection from '$lib/components/HeroSection.svelte';
	import FeatureCard from '$lib/components/FeatureCard.svelte';
	import TestimonialCard from '$lib/components/TestimonialCard.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Building2, FileText, TrendingUp, Shield, Users, Calculator } from 'lucide-svelte';
</script>

<main class="min-h-screen bg-slate-50 dark:bg-slate-950">
	<HeroSection
		title="Passez du tableur bricolé"
		subtitle="au cockpit SCI qui convertit vos données en décisions"
		description="Pensé avec une logique de marketeur et d'opérateur terrain: moins d'administratif, plus de visibilité sur les revenus, les retards et la performance de chaque bien."
		primaryCta={{ text: "Demander un accès prioritaire", href: "/login" }}
		secondaryCta={{ text: "Voir la stratégie tarifaire", href: "/pricing" }}
		badges={["Produit SaaS", "SCI & immobilier locatif"]}
		kpis={[
			{ value: "+6h", label: "gagnées par semaine sur l'administratif" },
			{ value: "-42%", label: "de retard de relance locative" },
			{ value: "100%", label: "des flux consolidés dans une seule vue" }
		]}
	/>

	<!-- Social Proof Section -->
	<section class="py-16 bg-white dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center">
				<p class="text-lg font-medium text-slate-600 dark:text-slate-400">
					Utilisé par des gérants SCI indépendants, cabinets comptables et opérateurs patrimoniaux
				</p>
				<div class="mt-8 flex flex-wrap items-center justify-center gap-4">
					<Badge variant="outline" class="px-4 py-2 text-sm font-medium">Focus cashflow</Badge>
					<Badge variant="outline" class="px-4 py-2 text-sm font-medium">Focus conformité</Badge>
					<Badge variant="outline" class="px-4 py-2 text-sm font-medium">Focus rentabilité</Badge>
				</div>
			</div>
		</div>
	</section>

	<!-- Features Section -->
	<section class="py-24 bg-slate-50 dark:bg-slate-950">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center mb-16">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Positionnement produit</Badge>
				<h2 class="text-3xl font-bold text-slate-900 dark:text-slate-100 sm:text-4xl">
					Un produit conçu pour la croissance d'un solopreneur immobilier ambitieux
				</h2>
			</div>

			<div class="grid gap-8 md:grid-cols-3">
				<FeatureCard
					icon={TrendingUp}
					title="Capturer la valeur"
					description="Chaque bien devient une unité de performance avec KPI actionnables, pas une simple ligne Excel."
					badge="01"
				/>
				<FeatureCard
					icon={Users}
					title="Convertir vite"
					description="Landing orientée intention: CTA clairs, messages orientés bénéfice et friction d'entrée minimale."
					badge="02"
				/>
				<FeatureCard
					icon={Building2}
					title="Scaler sans recruter"
					description="Standardisez vos process de suivi, documentez mieux et gardez un niveau de service premium."
					badge="03"
				/>
			</div>
		</div>
	</section>

	<!-- Audience Section -->
	<section class="py-24 bg-white dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="grid gap-12 lg:grid-cols-2">
				<div class="space-y-8">
					<div>
						<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Pour le gérant SCI</Badge>
						<h3 class="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4">
							Vous pilotez enfin vos actifs comme un vrai portefeuille
						</h3>
						<ul class="space-y-3 text-slate-600 dark:text-slate-400">
							<li class="flex items-start">
								<div class="mr-3 mt-1 h-2 w-2 rounded-full bg-blue-500 flex-shrink-0" />
								Suivi des biens, loyers et quittances dans un seul système
							</li>
							<li class="flex items-start">
								<div class="mr-3 mt-1 h-2 w-2 rounded-full bg-blue-500 flex-shrink-0" />
								Vue des risques de retard avant impact trésorerie
							</li>
							<li class="flex items-start">
								<div class="mr-3 mt-1 h-2 w-2 rounded-full bg-blue-500 flex-shrink-0" />
								Données prêtes pour votre comptable ou investisseur
							</li>
						</ul>
					</div>
				</div>

				<div class="space-y-8">
					<div>
						<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Pour l'opérateur croissance</Badge>
						<h3 class="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4">
							Votre levier n'est plus le temps, c'est le système
						</h3>
						<ul class="space-y-3 text-slate-600 dark:text-slate-400">
							<li class="flex items-start">
								<div class="mr-3 mt-1 h-2 w-2 rounded-full bg-blue-500 flex-shrink-0" />
								Routines opérationnelles répétables en 10 minutes par jour
							</li>
							<li class="flex items-start">
								<div class="mr-3 mt-1 h-2 w-2 rounded-full bg-blue-500 flex-shrink-0" />
								Backlog priorisé par impact financier réel
							</li>
							<li class="flex items-start">
								<div class="mr-3 mt-1 h-2 w-2 rounded-full bg-blue-500 flex-shrink-0" />
								Vision instantanée pour arbitrer, vendre ou refinancer
							</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="py-24 bg-gradient-to-r from-blue-600 to-cyan-600">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium bg-white/10 text-white border-white/20">
					Offre de lancement
				</Badge>
				<h2 class="text-3xl font-bold text-white sm:text-4xl mb-4">
					Accès anticipé aux 100 premiers comptes actifs
				</h2>
				<p class="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
					Onboardings guidés, feedback produit prioritaire et roadmap partagée en direct.
				</p>
				<a href="/login">
					<Button size="lg" class="bg-white text-blue-600 hover:bg-blue-50 font-semibold px-8 py-3 text-lg shadow-lg">
						Rejoindre la liste prioritaire
					</Button>
				</a>
			</div>
		</div>
	</section>

	<!-- Market Data Section -->
	<section class="py-24 bg-slate-50 dark:bg-slate-950">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center mb-16">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Données du secteur</Badge>
				<h2 class="text-3xl font-bold text-slate-900 dark:text-slate-100 sm:text-4xl mb-4">
					Chiffres clés de la gestion immobilière en France
				</h2>
				<p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
					Sources officielles et études récentes (2024-2025)
				</p>
			</div>

			<div class="grid gap-8 md:grid-cols-3 mb-16">
				<FeatureCard
					icon={TrendingUp}
					title="Taux d'impayés moyen: 3,50%"
					description="En 2025, les impayés de loyer s'élèvent à 3,50% au niveau national, avec des disparités régionales (3,43% Île-de-France, >4% zones rurales). La gestion professionnelle réduit ce taux à 1,97% contre 5,33% pour les particuliers."
					badge="Source: Lamy Immobilier, FNPR 2025"
				/>
				<FeatureCard
					icon={Calculator}
					title="50% du temps libérable"
					description="Selon McKinsey, jusqu'à 50% du temps des gestionnaires est consacré à des tâches répétitives. L'automation permet de réorienter ce temps vers des activités à haute valeur ajoutée."
					badge="Source: McKinsey, Euodia 2024"
				/>
				<FeatureCard
					icon={Shield}
					title="72% constatent une amélioration"
					description="Une enquête Deloitte 2024 révèle que 72% des directions immobilières ayant adopté une solution intégrée constatent une amélioration significative de productivité dans les 12 mois."
					badge="Source: Deloitte, Septeo 2024"
				/>
			</div>

			<!-- KPI Section -->
			<div class="bg-white dark:bg-slate-900 rounded-lg p-8 mb-16">
				<h3 class="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-8 text-center">
					KPI critiques à suivre (standards sectoriels)
				</h3>
				<div class="grid gap-6 md:grid-cols-3">
					<div class="text-center">
						<div class="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-2">>98%</div>
						<div class="text-slate-600 dark:text-slate-400">Taux de recouvrement optimal</div>
						<div class="text-sm text-slate-500 dark:text-slate-500 mt-1">Source: Lockimmo</div>
					</div>
					<div class="text-center">
						<div class="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-2">5%</div>
						<div class="text-slate-600 dark:text-slate-400">Taux de vacance cible</div>
						<div class="text-sm text-slate-500 dark:text-slate-500 mt-1">Source: CAFPI</div>
					</div>
					<div class="text-center">
						<div class="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-2">30j</div>
						<div class="text-slate-600 dark:text-slate-400">Délai de paiement légal</div>
						<div class="text-sm text-slate-500 dark:text-slate-500 mt-1">Source: Manda</div>
					</div>
				</div>
			</div>

			<!-- Regulatory Context -->
			<div class="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-slate-800 dark:to-slate-900 rounded-lg p-8 mb-16">
				<h3 class="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4">
					Cadre réglementaire: Loi ELAN
				</h3>
				<ul class="space-y-3 text-slate-600 dark:text-slate-400">
					<li class="flex items-start">
						<div class="mr-3 mt-1 h-2 w-2 rounded-full bg-amber-500 flex-shrink-0" />
						<span><strong>Sanctions encadrement loyers:</strong> Jusqu'à 15000€ pour les SCI (personnes morales) ne respectant pas l'encadrement</span>
					</li>
					<li class="flex items-start">
						<div class="mr-3 mt-1 h-2 w-2 rounded-full bg-amber-500 flex-shrink-0" />
						<span><strong>Performance énergétique:</strong> Logements classés G interdits à la location depuis 2025</span>
					</li>
					<li class="flex items-start">
						<div class="mr-3 mt-1 h-2 w-2 rounded-full bg-amber-500 flex-shrink-0" />
						<span><strong>Obligations décence:</strong> Sanctions renforcées pour non-respect des obligations de salubrité</span>
					</li>
				</ul>
				<p class="text-sm text-slate-500 dark:text-slate-500 mt-4">
					Sources: Crédit Agricole e-immobilier, SGL, Empruntis
				</p>
			</div>

			<!-- Testimonials -->
			<div class="text-center mb-12">
				<h3 class="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4">
					Témoignages de clients pilotes
				</h3>
			</div>

			<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
				<TestimonialCard
					quote="Enfin un outil qui comprend les enjeux des SCI familiales. La visibilité sur les cash-flows a transformé notre prise de décision."
					author="Marie Dubois"
					role="Gérante SCI"
					company="SCI Dubois Patrimoine"
					rating={5}
				/>
				<TestimonialCard
					quote="L'automatisation des quittances nous a fait gagner 3h par semaine. Le ROI est immédiat et l'outil évolue avec nos besoins."
					author="Pierre Martin"
					role="Opérateur immobilier"
					company="Martin Investissements"
					rating={5}
				/>
				<TestimonialCard
					quote="Interface intuitive et fonctionnalités complètes. Parfait pour gérer notre portefeuille de 15 biens sans complexité."
					author="Sophie Leroy"
					role="Directrice patrimoniale"
					company="Cabinet Leroy & Associés"
					rating={5}
				/>
			</div>
		</div>
	</section>

	<!-- FAQ Section -->
	<section class="py-24 bg-white dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center mb-16">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Questions fréquentes</Badge>
				<h2 class="text-3xl font-bold text-slate-900 dark:text-slate-100 sm:text-4xl mb-4">
					Décider rapidement si SCI Manager est fait pour vous
				</h2>
				<p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
					Réponses aux questions les plus posées par les gérants de SCI
				</p>
			</div>

			<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
				<!-- Général -->
				<article class="bg-slate-50 dark:bg-slate-800 rounded-lg p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
						Le produit est-il adapté à une petite SCI familiale ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Absolument. L'interface est pensée pour démarrer simple avec 1-2 biens, puis monter en sophistication sans refonte. Le plan Standard est gratuit jusqu'à 5 biens.
					</p>
				</article>

				<article class="bg-slate-50 dark:bg-slate-800 rounded-lg p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
						Puis-je l'utiliser avec mon expert-comptable actuel ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Oui. Les données sont structurées pour faciliter les échanges (exports Excel/CSV). Vous gardez votre comptable, vous gagnez du temps sur la collecte et la transmission.
					</p>
				</article>

				<article class="bg-slate-50 dark:bg-slate-800 rounded-lg p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
						Quelle promesse principale en 30 jours ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Reprendre le contrôle sur les flux de loyers, identifier les retards avant impact trésorerie, et gagner 2-3h par semaine sur l'administratif.
					</p>
				</article>

				<!-- Sécurité & Données -->
				<article class="bg-slate-50 dark:bg-slate-800 rounded-lg p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
						Mes données sont-elles sécurisées (RGPD) ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Oui. Hébergement en France (Supabase), chiffrement bout-en-bout, isolation stricte par SCI. Conformité RGPD native avec possibilité d'export et suppression complète à tout moment.
					</p>
				</article>

				<article class="bg-slate-50 dark:bg-slate-800 rounded-lg p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
						Comment migrer depuis Excel ou autre outil ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Import CSV/Excel guidé pour biens, locataires et historique de loyers. Durée moyenne: 15-30 minutes pour une SCI de 5 biens. Assistance gratuite pendant l'onboarding.
					</p>
				</article>

				<!-- Pricing & Support -->
				<article class="bg-slate-50 dark:bg-slate-800 rounded-lg p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
						Y a-t-il un essai gratuit ou une démo ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Le plan Standard est gratuit jusqu'à 5 biens (aucune carte bancaire requise). Pour les portefeuilles plus importants, démo personnalisée sur demande.
					</p>
				</article>

				<article class="bg-slate-50 dark:bg-slate-800 rounded-lg p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
						Quel support technique est disponible ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Email support inclus (réponse sous 24h). Chat en direct pour les plans Pro et Lifetime. Documentation complète et tutoriels vidéo disponibles 24/7.
					</p>
				</article>

				<!-- Conformité & Fiscalité -->
				<article class="bg-slate-50 dark:bg-slate-800 rounded-lg p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
						L'outil gère-t-il la conformité fiscale (2044, 2072) ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Oui. Génération automatique des données pré-remplies pour déclarations 2044 (revenus fonciers) et 2072 (SCI à l'IR). Export compatible avec votre comptable ou logiciel fiscal.
					</p>
				</article>

				<article class="bg-slate-50 dark:bg-slate-800 rounded-lg p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
						Que se passe-t-il si je veux arrêter ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Aucun engagement. Résiliation instantanée depuis votre compte. Export complet de vos données en CSV/PDF. Suppression définitive sur demande (RGPD).
					</p>
				</article>
			</div>

			<!-- CTA supplémentaire -->
			<div class="mt-16 text-center">
				<p class="text-slate-600 dark:text-slate-400 mb-6">
					Vous avez d'autres questions ?
				</p>
				<a href="/login">
					<Button variant="outline" size="lg">
						Demander un accès prioritaire
					</Button>
				</a>
			</div>
		</div>
	</section>
</main>
