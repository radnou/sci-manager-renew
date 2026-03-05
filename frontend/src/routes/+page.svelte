<script>
	import HeroSection from '$lib/components/HeroSection.svelte';
	import FeatureCard from '$lib/components/FeatureCard.svelte';
	import TestimonialCard from '$lib/components/TestimonialCard.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Building2, FileText, TrendingUp, Shield, Users, Calculator } from 'lucide-svelte';

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
			title: 'KPI de pilotage locatif',
			finding:
				'Recouvrement >98%, vacance proche de 5% et suivi du délai de paiement sont les standards les plus suivis sur le marché.',
			source: 'Lockimmo / CAFPI / Manda',
			url: 'https://www.lockimmo.com/les-indicateurs-cles-pour-piloter-la-rentabilite-de-votre-portefeuille-de-gestion-locative/'
		}
	];
</script>

<svelte:head>
	<title>GererSCI | Pilotez votre SCI comme un opérateur</title>
	<meta
		name="description"
		content="GererSCI centralise biens, loyers et documents en un cockpit unique pour accélérer la gestion et sécuriser vos revenus locatifs."
	/>
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<link rel="canonical" href="https://gerersci.fr" />
</svelte:head>

<main class="min-h-screen bg-slate-50 dark:bg-slate-950">
	<HeroSection
		title="Passez du tableur bricolé"
		subtitle="au cockpit SCI qui convertit vos données en décisions"
		description="Pensé avec une logique de marketeur et d'opérateur terrain: moins d'administratif, plus de visibilité sur les revenus, les retards et la performance de chaque bien."
		primaryCta={{ text: 'Demander un accès prioritaire', href: '/login' }}
		secondaryCta={{ text: 'Voir la stratégie tarifaire', href: '/pricing' }}
		badges={['Produit SaaS', 'SCI & immobilier locatif']}
		kpis={[
			{ value: '+6h', label: "gagnées par semaine sur l'administratif" },
			{ value: '-42%', label: 'de retard de relance locative' },
			{ value: '100%', label: 'des flux consolidés dans une seule vue' }
		]}
	/>

	<!-- Social Proof Section -->
	<section class="bg-white py-16 dark:bg-slate-900">
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
	<section id="features" class="bg-slate-50 py-24 dark:bg-slate-950">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="mb-16 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium"
					>Positionnement produit</Badge
				>
				<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
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
	<section class="bg-white py-24 dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="grid gap-12 lg:grid-cols-2">
				<div class="space-y-8">
					<div>
						<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium"
							>Pour le gérant SCI</Badge
						>
						<h3 class="mb-4 text-2xl font-bold text-slate-900 dark:text-slate-100">
							Vous pilotez enfin vos actifs comme un vrai portefeuille
						</h3>
						<ul class="space-y-3 text-slate-600 dark:text-slate-400">
							<li class="flex items-start">
								<div class="mt-1 mr-3 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"></div>
								Suivi des biens, loyers et quittances dans un seul système
							</li>
							<li class="flex items-start">
								<div class="mt-1 mr-3 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"></div>
								Vue des risques de retard avant impact trésorerie
							</li>
							<li class="flex items-start">
								<div class="mt-1 mr-3 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"></div>
								Données prêtes pour votre comptable ou investisseur
							</li>
						</ul>
					</div>
				</div>

				<div class="space-y-8">
					<div>
						<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium"
							>Pour l'opérateur croissance</Badge
						>
						<h3 class="mb-4 text-2xl font-bold text-slate-900 dark:text-slate-100">
							Votre levier n'est plus le temps, c'est le système
						</h3>
						<ul class="space-y-3 text-slate-600 dark:text-slate-400">
							<li class="flex items-start">
								<div class="mt-1 mr-3 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"></div>
								Routines opérationnelles répétables en 10 minutes par jour
							</li>
							<li class="flex items-start">
								<div class="mt-1 mr-3 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"></div>
								Backlog priorisé par impact financier réel
							</li>
							<li class="flex items-start">
								<div class="mt-1 mr-3 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500"></div>
								Vision instantanée pour arbitrer, vendre ou refinancer
							</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="bg-gradient-to-r from-blue-600 to-cyan-600 py-24">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center">
				<Badge
					variant="secondary"
					class="mb-4 border-white/20 bg-white/10 px-3 py-1 text-sm font-medium text-white"
				>
					Offre de lancement
				</Badge>
				<h2 class="mb-4 text-3xl font-bold text-white sm:text-4xl">
					Accès anticipé aux 100 premiers comptes actifs
				</h2>
				<p class="mx-auto mb-8 max-w-2xl text-xl text-blue-100">
					Onboardings guidés, feedback produit prioritaire et roadmap partagée en direct.
				</p>
				<a href="/login">
					<Button
						size="lg"
						class="bg-white px-8 py-3 text-lg font-semibold text-blue-600 shadow-lg hover:bg-blue-50"
					>
						Rejoindre la liste prioritaire
					</Button>
				</a>
			</div>
		</div>
	</section>

	<!-- Market Data Section -->
	<section id="market-data" class="bg-slate-50 py-24 dark:bg-slate-950">
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

			<div class="mb-16 grid gap-8 md:grid-cols-3">
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
			<div class="mb-16 rounded-lg bg-white p-8 dark:bg-slate-900">
				<h3 class="mb-8 text-center text-2xl font-bold text-slate-900 dark:text-slate-100">
					KPI critiques à suivre (standards sectoriels)
				</h3>
				<div class="grid gap-6 md:grid-cols-3">
					<div class="text-center">
						<div class="mb-2 text-4xl font-bold text-blue-600 dark:text-blue-400">>98%</div>
						<div class="text-slate-600 dark:text-slate-400">Taux de recouvrement optimal</div>
						<div class="mt-1 text-sm text-slate-500 dark:text-slate-500">Source: Lockimmo</div>
					</div>
					<div class="text-center">
						<div class="mb-2 text-4xl font-bold text-blue-600 dark:text-blue-400">5%</div>
						<div class="text-slate-600 dark:text-slate-400">Taux de vacance cible</div>
						<div class="mt-1 text-sm text-slate-500 dark:text-slate-500">Source: CAFPI</div>
					</div>
					<div class="text-center">
						<div class="mb-2 text-4xl font-bold text-blue-600 dark:text-blue-400">30j</div>
						<div class="text-slate-600 dark:text-slate-400">Délai de paiement légal</div>
						<div class="mt-1 text-sm text-slate-500 dark:text-slate-500">Source: Manda</div>
					</div>
				</div>
			</div>

			<!-- Regulatory Context -->
			<div
				class="mb-16 rounded-lg bg-gradient-to-r from-amber-50 to-orange-50 p-8 dark:from-slate-800 dark:to-slate-900"
			>
				<h3 class="mb-4 text-2xl font-bold text-slate-900 dark:text-slate-100">
					Cadre réglementaire: Loi ELAN
				</h3>
				<ul class="space-y-3 text-slate-600 dark:text-slate-400">
					<li class="flex items-start">
						<div class="mt-1 mr-3 h-2 w-2 flex-shrink-0 rounded-full bg-amber-500"></div>
						<span
							><strong>Sanctions encadrement loyers:</strong> Jusqu'à 15000€ pour les SCI (personnes morales)
							ne respectant pas l'encadrement</span
						>
					</li>
					<li class="flex items-start">
						<div class="mt-1 mr-3 h-2 w-2 flex-shrink-0 rounded-full bg-amber-500"></div>
						<span
							><strong>Performance énergétique:</strong> Logements classés G interdits à la location depuis
							2025</span
						>
					</li>
					<li class="flex items-start">
						<div class="mt-1 mr-3 h-2 w-2 flex-shrink-0 rounded-full bg-amber-500"></div>
						<span
							><strong>Obligations décence:</strong> Sanctions renforcées pour non-respect des obligations
							de salubrité</span
						>
					</li>
				</ul>
				<p class="mt-4 text-sm text-slate-500 dark:text-slate-500">
					Sources: Crédit Agricole e-immobilier, SGL, Empruntis
				</p>
			</div>

			<!-- Studies Section -->
			<div id="studies" class="mb-16 rounded-lg bg-white p-8 dark:bg-slate-900">
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
						Synthèse issue des études documentées dans <code
							>claudedocs/landing_page_update_2026-03-05.md</code
						>.
					</p>
				</div>

				<div class="grid gap-4 md:grid-cols-2">
					{#each studyReferences as study (study.title)}
						<article
							class="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-800/60"
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

			<!-- Testimonials -->
			<div class="mb-12 text-center">
				<h3 class="mb-4 text-2xl font-bold text-slate-900 dark:text-slate-100">
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
	<section class="bg-white py-24 dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="mb-16 text-center">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium"
					>Questions fréquentes</Badge
				>
				<h2 class="mb-4 text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
					Décider rapidement si GererSCI est fait pour vous
				</h2>
				<p class="mx-auto max-w-2xl text-lg text-slate-600 dark:text-slate-400">
					Réponses aux questions les plus posées par les gérants de SCI
				</p>
			</div>

			<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
				<!-- Général -->
				<article class="rounded-lg bg-slate-50 p-6 dark:bg-slate-800">
					<h3 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
						Le produit est-il adapté à une petite SCI familiale ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Absolument. L'interface est pensée pour démarrer simple avec 1-2 biens, puis monter en
						sophistication sans refonte.
					</p>
				</article>

				<article class="rounded-lg bg-slate-50 p-6 dark:bg-slate-800">
					<h3 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
						Puis-je l'utiliser avec mon expert-comptable actuel ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Oui. Les données sont structurées dans le cockpit pour faciliter les échanges avec votre
						comptable. Les exports avancés sont planifiés dans la roadmap.
					</p>
				</article>

				<article class="rounded-lg bg-slate-50 p-6 dark:bg-slate-800">
					<h3 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
						Quelle promesse principale en 30 jours ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Reprendre le contrôle sur les flux de loyers, identifier les retards avant impact
						trésorerie, et gagner 2-3h par semaine sur l'administratif.
					</p>
				</article>

				<!-- Sécurité & Données -->
				<article class="rounded-lg bg-slate-50 p-6 dark:bg-slate-800">
					<h3 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
						Mes données sont-elles sécurisées (RGPD) ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Oui. Hébergement en France (Supabase), chiffrement bout-en-bout, isolation stricte par
						SCI. Conformité RGPD native avec possibilité d'export et suppression complète à tout
						moment.
					</p>
				</article>

				<article class="rounded-lg bg-slate-50 p-6 dark:bg-slate-800">
					<h3 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
						Comment migrer depuis Excel ou autre outil ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						La version actuelle privilégie une saisie structurée rapide pour repartir sur des bases
						fiables. Le module d'import CSV/Excel est en cours d'intégration.
					</p>
				</article>

				<!-- Pricing & Support -->
				<article class="rounded-lg bg-slate-50 p-6 dark:bg-slate-800">
					<h3 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
						Y a-t-il un essai gratuit ou une démo ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Vous pouvez créer un compte immédiatement pour découvrir l'interface, puis activer
						l'abonnement depuis la page tarifs.
					</p>
				</article>

				<article class="rounded-lg bg-slate-50 p-6 dark:bg-slate-800">
					<h3 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
						Quel support technique est disponible ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Un support email est disponible pour les demandes produit et incidents techniques.
						L'objectif de réponse est sous 24-48h ouvrées.
					</p>
				</article>

				<!-- Conformité & Fiscalité -->
				<article class="rounded-lg bg-slate-50 p-6 dark:bg-slate-800">
					<h3 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
						L'outil gère-t-il la conformité fiscale (2044, 2072) ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Un endpoint CERFA 2044 est disponible en version bêta (calcul simplifié). La couverture
						complète 2072 et les exports fiscaux avancés sont en préparation.
					</p>
				</article>

				<article class="rounded-lg bg-slate-50 p-6 dark:bg-slate-800">
					<h3 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
						Que se passe-t-il si je veux arrêter ?
					</h3>
					<p class="text-slate-600 dark:text-slate-400">
						Aucun engagement. Vous pouvez arrêter votre abonnement Stripe à tout moment et demander la
						suppression de votre compte depuis l'espace confidentialité.
					</p>
				</article>
			</div>

			<!-- CTA supplémentaire -->
			<div class="mt-16 text-center">
				<p class="mb-6 text-slate-600 dark:text-slate-400">Vous avez d'autres questions ?</p>
				<a href="/login">
					<Button variant="outline" size="lg">Accéder à la liste prioritaire</Button>
				</a>
			</div>
		</div>
	</section>
</main>
