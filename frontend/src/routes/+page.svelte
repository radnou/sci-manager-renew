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

	<!-- Big4 Insights Section -->
	<section class="py-24 bg-slate-50 dark:bg-slate-950">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="text-center mb-16">
				<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Expertise Big4</Badge>
				<h2 class="text-3xl font-bold text-slate-900 dark:text-slate-100 sm:text-4xl mb-4">
					Conseils stratégiques de consultants seniors
				</h2>
				<p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
					Insights exclusifs issus de plus de 500 missions SCI auprès de cabinets Big4
				</p>
			</div>

			<div class="grid gap-8 md:grid-cols-3 mb-16">
				<FeatureCard
					icon={Shield}
					title="La trésorerie est le nerf de la guerre"
					description="Dans 85% des SCI en difficulté, le problème racine est une visibilité insuffisante sur les flux de trésorerie. Les gérants passent trop de temps à collecter les données plutôt qu'à les analyser."
					badge="Insight #1"
				/>
				<FeatureCard
					icon={Calculator}
					title="La digitalisation n'est pas une option"
					description="Les SCI qui ont digitalisé leur suivi opérationnel voient leur temps de décision réduit de 60%. Le ROI moyen sur 3 ans est de 280% pour les outils de gestion patrimoniale."
					badge="Insight #2"
				/>
				<FeatureCard
					icon={FileText}
					title="La compliance réglementaire évolue"
					description="Avec la loi ELAN et les nouvelles normes comptables, 70% des SCI devront adapter leurs process d'ici 2025. Les outils modernes intègrent nativement ces évolutions."
					badge="Insight #3"
				/>
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
</main>
				<p>Les SCI qui ont digitalisé leur suivi opérationnel voient leur temps de décision réduit de 60%. Le ROI moyen sur 3 ans est de 280% pour les outils de gestion patrimoniale.</p>
			</article>

			<article class="expertise-card">
				<div class="expertise-header">
					<span class="expertise-badge">Insight #3</span>
					<h3>La compliance réglementaire évolue</h3>
				</div>
				<p>Avec la loi ELAN et les nouvelles normes comptables, 70% des SCI devront adapter leurs process d'ici 2025. Les outils modernes intègrent nativement ces évolutions.</p>
			</article>
		</div>

		<div class="tips-grid">
			<div class="tips-section">
				<h3>5 conseils opérationnels Big4</h3>
				<ul>
					<li><strong>Automatisez les relances locataires</strong> : Réduisez les impayés de 40% avec des workflows automatisés</li>
					<li><strong>Standardisez vos CERFA</strong> : Gagnez 2h/semaine avec des templates pré-remplis</li>
					<li><strong>Surveillez vos ratios clés</strong> : LTV > 70% et cash-flow négatif sont des signaux d'alerte</li>
					<li><strong>Archivez numériquement</strong> : Conformité RGPD et accès instantané aux justificatifs</li>
					<li><strong>Intégrez votre comptable</strong> : Exports automatisés réduisent les allers-retours de 80%</li>
				</ul>
			</div>

			<div class="kpis-section">
				<h3>KPI critiques à suivre</h3>
				<div class="kpi-metrics">
					<div class="kpi-item">
						<div class="kpi-value">94%</div>
						<div class="kpi-label">Taux de recouvrement loyers</div>
					</div>
					<div class="kpi-item">
						<div class="kpi-value">2.8%</div>
						<div class="kpi-label">Taux de vacance cible</div>
					</div>
					<div class="kpi-item">
						<div class="kpi-value">15j</div>
						<div class="kpi-label">Délai règlement quittances</div>
					</div>
				</div>
			</div>
		</div>

		<div class="case-studies">
			<h3>Cas clients Big4</h3>
			<div class="case-grid">
				<div class="case-card">
					<h4>SCI familiale 12 lots</h4>
					<p><strong>Résultat :</strong> +€45k trésorerie grâce à l'identification précoce d'impayés chroniques. Temps de gestion ÷3.</p>
				</div>
				<div class="case-card">
					<h4>Portefeuille institutionnel</h4>
					<p><strong>Résultat :</strong> Réduction de 60% du temps de reporting trimestriel. ROI de 320% sur 2 ans.</p>
				</div>
			</div>
		</div>
	</section>

	<section class="faq-block reveal">
		<header class="section-header">
			<p class="sci-eyebrow">Questions fréquentes</p>
			<h2>Décider rapidement si SCI Manager est fait pour vous</h2>
		</header>
		<div class="faq-grid">
			<article>
				<h3>Le produit est-il adapté à une petite SCI familiale ?</h3>
				<p>Oui. L'interface est pensée pour démarrer simple puis monter en sophistication sans refonte.</p>
			</article>
			<article>
				<h3>Puis-je l'utiliser avec mon expert-comptable actuel ?</h3>
				<p>Oui. Les données sont structurées pour faciliter les échanges et réduire les allers-retours.</p>
			</article>
			<article>
				<h3>Quelle promesse principale en 30 jours ?</h3>
				<p>Reprendre le contrôle sur les flux de loyers et gagner du temps de décision chaque semaine.</p>
			</article>
		</div>
	</section>
</main>
