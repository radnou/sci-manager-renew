<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import EmailCapture from '$lib/components/EmailCapture.svelte';
	import {
		ArrowRight,
		CalendarDays,
		FileText,
		Calculator,
		Landmark,
		ClipboardCheck,
		Users,
		TrendingUp,
		Home,
		Receipt,
		BookOpen,
		AlertTriangle
	} from 'lucide-svelte';

	type Urgency = 'info' | 'attention' | 'critique';

	// Email gate: show first 4 months free, rest after email
	let emailUnlocked = $state(false);
	const FREE_MONTHS = 4;

	interface FiscalEvent {
		mois: string;
		titre: string;
		description: string;
		urgence: Urgency;
		icon: typeof CalendarDays;
	}

	const evenements: FiscalEvent[] = [
		{
			mois: 'Janvier',
			titre: 'Bilan comptable N-1 (SCI IS)',
			description:
				"Préparez la clôture comptable de l'exercice précédent. Rassemblez les pièces justificatives, relevés bancaires et factures pour établir le bilan et le compte de résultat.",
			urgence: 'info',
			icon: BookOpen
		},
		{
			mois: 'Février',
			titre: 'Préparation déclaration 2044 / 2072',
			description:
				'Compilez les revenus fonciers, charges déductibles, intérêts d\'emprunt et travaux. Formulaire 2044 pour les SCI à l\'IR, formulaire 2072 pour les SCI à l\'IS.',
			urgence: 'attention',
			icon: FileText
		},
		{
			mois: 'Mars',
			titre: 'Clôture exercice N-1 possible',
			description:
				'Date limite courante pour clôturer l\'exercice comptable si votre SCI ne clôture pas au 31 décembre. Vérifiez vos statuts.',
			urgence: 'info',
			icon: ClipboardCheck
		},
		{
			mois: 'Avril',
			titre: 'Ouverture déclaration de revenus',
			description:
				'Le service de déclaration en ligne ouvre sur impots.gouv.fr. Préparez vos identifiants et les éléments de votre déclaration 2044.',
			urgence: 'attention',
			icon: Landmark
		},
		{
			mois: 'Mai',
			titre: 'Date limite déclaration 2044 / 2072',
			description:
				'Échéance de la déclaration en ligne par zones : zone 1 (dép. 01–19 + non-résidents), zone 2 (dép. 20–54), zone 3 (dép. 55–976). Dates exactes à vérifier sur impots.gouv.fr.',
			urgence: 'critique',
			icon: AlertTriangle
		},
		{
			mois: 'Juin',
			titre: 'Date limite papier & acomptes IS',
			description:
				'Dernier délai pour les déclarations papier. Pour les SCI à l\'IS : paiement du 2e acompte d\'impôt sur les sociétés.',
			urgence: 'critique',
			icon: Calculator
		},
		{
			mois: 'Juillet',
			titre: 'Avis d\'imposition',
			description:
				'Réception de l\'avis d\'imposition sur le revenu. Vérifiez que vos revenus fonciers ont été correctement pris en compte.',
			urgence: 'info',
			icon: Receipt
		},
		{
			mois: 'Septembre',
			titre: 'Assemblée générale annuelle',
			description:
				'Si votre SCI clôture au 31/12, vous devez tenir l\'AG d\'approbation des comptes dans les 6 mois suivant la clôture. Rédigez le procès-verbal.',
			urgence: 'attention',
			icon: Users
		},
		{
			mois: 'Octobre',
			titre: 'Révision IRL (indice T3)',
			description:
				'Publication de l\'Indice de Référence des Loyers du 3e trimestre par l\'INSEE. Base de calcul pour la révision annuelle des loyers de vos baux.',
			urgence: 'info',
			icon: TrendingUp
		},
		{
			mois: 'Novembre',
			titre: 'Taxe foncière',
			description:
				'Date limite de paiement de la taxe foncière (mi-octobre pour le papier, mi-novembre en ligne). Charge déductible des revenus fonciers.',
			urgence: 'critique',
			icon: Home
		},
		{
			mois: 'Décembre',
			titre: 'Clôture exercice (31/12)',
			description:
				'Fin de l\'exercice comptable standard. Arrêtez les comptes, provisionnez les charges à payer et préparez la transition vers le nouvel exercice.',
			urgence: 'info',
			icon: CalendarDays
		}
	];

	const urgenceStyles: Record<Urgency, { border: string; bg: string; badge: string; badgeText: string; icon: string }> = {
		info: {
			border: 'border-emerald-200 dark:border-emerald-800',
			bg: 'bg-emerald-50/50 dark:bg-emerald-950/20',
			badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
			badgeText: 'Information',
			icon: 'text-emerald-600 dark:text-emerald-400'
		},
		attention: {
			border: 'border-amber-200 dark:border-amber-800',
			bg: 'bg-amber-50/50 dark:bg-amber-950/20',
			badge: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
			badgeText: 'Attention',
			icon: 'text-amber-600 dark:text-amber-400'
		},
		critique: {
			border: 'border-rose-200 dark:border-rose-800',
			bg: 'bg-rose-50/50 dark:bg-rose-950/20',
			badge: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300',
			badgeText: 'Deadline',
			icon: 'text-rose-600 dark:text-rose-400'
		}
	};
</script>

<svelte:head>
	<title>Calendrier fiscal SCI 2026 — Dates cl&eacute;s et obligations | G&eacute;rerSCI</title>
	<meta
		name="description"
		content="Calendrier fiscal SCI 2026 : toutes les dates cl&eacute;s pour g&eacute;rer votre SCI. D&eacute;claration 2044, 2072, taxe fonci&egrave;re, assembl&eacute;e g&eacute;n&eacute;rale, r&eacute;vision IRL. Gratuit."
	/>
	<link rel="canonical" href="https://gerersci.fr/calendrier-fiscal" />
	<meta property="og:title" content="Calendrier fiscal SCI 2026 — Dates cl&eacute;s et obligations" />
	<meta
		property="og:description"
		content="Toutes les &eacute;ch&eacute;ances fiscales et obligations pour votre SCI en 2026. D&eacute;claration 2044, 2072, taxe fonci&egrave;re, AG, IRL."
	/>
	<meta property="og:url" content="https://gerersci.fr/calendrier-fiscal" />
	<meta property="og:type" content="website" />
</svelte:head>

<main class="min-h-screen bg-slate-50 dark:bg-slate-950">
	<!-- Header -->
	<section class="relative overflow-hidden bg-white py-16 sm:py-20 dark:bg-slate-900">
		<div
			class="pointer-events-none absolute inset-0 bg-gradient-to-br from-blue-50/80 via-transparent to-cyan-50/60 dark:from-blue-950/30 dark:to-cyan-950/20"
		></div>
		<div class="relative mx-auto max-w-4xl px-4 text-center sm:px-6">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">
				2026 &middot; Gratuit &middot; Sans inscription
			</Badge>
			<h1
				class="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl dark:text-white"
			>
				Calendrier fiscal
				<span class="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
					SCI 2026
				</span>
			</h1>
			<p class="mt-4 text-lg text-slate-600 dark:text-slate-400">
				Toutes les dates cl&eacute;s et obligations pour g&eacute;rer votre SCI sereinement.
			</p>

			<!-- Legend -->
			<div class="mt-8 flex flex-wrap items-center justify-center gap-4 text-sm">
				<span class="flex items-center gap-1.5">
					<span class="inline-block h-3 w-3 rounded-full bg-emerald-500"></span>
					<span class="text-slate-600 dark:text-slate-400">Information</span>
				</span>
				<span class="flex items-center gap-1.5">
					<span class="inline-block h-3 w-3 rounded-full bg-amber-500"></span>
					<span class="text-slate-600 dark:text-slate-400">Attention</span>
				</span>
				<span class="flex items-center gap-1.5">
					<span class="inline-block h-3 w-3 rounded-full bg-rose-500"></span>
					<span class="text-slate-600 dark:text-slate-400">Deadline critique</span>
				</span>
			</div>
		</div>
	</section>

	<!-- Timeline -->
	<section class="py-12 sm:py-16">
		<div class="mx-auto max-w-4xl px-4 sm:px-6">
			<!-- Timeline line (visible on md+) -->
			<div class="relative">
				<div
					class="absolute left-6 top-0 hidden h-full w-0.5 bg-gradient-to-b from-blue-200 via-slate-200 to-blue-200 md:block dark:from-blue-800 dark:via-slate-700 dark:to-blue-800"
				></div>

				<div class="space-y-6">
					{#each evenements as evt, i}
					{#if i >= FREE_MONTHS && !emailUnlocked}
						{#if i === FREE_MONTHS}
							<!-- Email gate -->
							<div class="relative md:pl-16">
								<div class="rounded-2xl border border-blue-200 bg-blue-50 p-6 text-center dark:border-blue-800 dark:bg-blue-950/30">
									<p class="mb-3 text-sm font-medium text-blue-800 dark:text-blue-200">
										{evenements.length - FREE_MONTHS} échéances restantes masquées
									</p>
									<EmailCapture
										source="calendrier-fiscal"
										title="Voir toutes les échéances"
										description="Entrez votre email pour débloquer le calendrier fiscal complet."
										buttonText="Débloquer le calendrier"
										onCaptured={() => (emailUnlocked = true)}
									/>
								</div>
							</div>
						{/if}
					{:else}
						{@const style = urgenceStyles[evt.urgence]}
						<div class="group relative md:pl-16">
							<!-- Timeline dot (visible on md+) -->
							<div
								class="absolute left-4 top-6 hidden h-5 w-5 items-center justify-center rounded-full border-2 border-white bg-slate-200 shadow-sm md:flex dark:border-slate-900 dark:bg-slate-700"
							>
								<div class="h-2 w-2 rounded-full {evt.urgence === 'critique' ? 'bg-rose-500' : evt.urgence === 'attention' ? 'bg-amber-500' : 'bg-emerald-500'}"></div>
							</div>

							<div
								class="rounded-2xl border {style.border} {style.bg} p-5 shadow-sm transition-shadow hover:shadow-md sm:p-6"
							>
								<div class="flex items-start gap-4">
									<!-- Icon -->
									<div
										class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white shadow-sm dark:bg-slate-800"
									>
										<evt.icon class="h-5 w-5 {style.icon}" />
									</div>

									<!-- Content -->
									<div class="min-w-0 flex-1">
										<div class="mb-1 flex flex-wrap items-center gap-2">
											<span
												class="text-sm font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400"
											>
												{evt.mois}
											</span>
											<span
												class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {style.badge}"
											>
												{style.badgeText}
											</span>
										</div>
										<h2 class="text-base font-bold text-slate-900 sm:text-lg dark:text-slate-100">
											{evt.titre}
										</h2>
										<p class="mt-1.5 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
											{evt.description}
										</p>
									</div>
								</div>
							</div>
						</div>
					{/if}
					{/each}
				</div>
			</div>
		</div>
	</section>

	<!-- Email capture + CTA -->
	<section class="pb-12 sm:pb-16">
		<div class="mx-auto max-w-2xl px-4 sm:px-6">
			<div
				class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 dark:border-slate-700 dark:bg-slate-800"
			>
				<div class="mb-6 text-center">
					<h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
						Ne manquez aucune &eacute;ch&eacute;ance
					</h2>
					<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
						Recevez un rappel avant chaque date cl&eacute; directement dans votre bo&icirc;te mail.
					</p>
				</div>

				{#if !emailUnlocked}
					<EmailCapture
						source="calendrier-fiscal"
						title="Voir le calendrier complet"
						description="Entrez votre email pour acc&eacute;der aux 12 mois d'&eacute;ch&eacute;ances fiscales."
						buttonText="D&eacute;bloquer"
						onCaptured={() => (emailUnlocked = true)}
					/>
				{:else}
					<p class="text-center text-sm text-emerald-600 dark:text-emerald-400">
						Calendrier complet d&eacute;bloqu&eacute;
					</p>
				{/if}

				<!-- CTA -->
				<div
					class="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-5 text-center dark:border-slate-700 dark:bg-slate-900"
				>
					<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">
						Automatisez vos &eacute;ch&eacute;ances avec G&eacute;rerSCI
					</p>
					<p class="mb-4 text-xs text-slate-500 dark:text-slate-400">
						Alertes automatiques, d&eacute;claration 2044 pr&eacute;-remplie, suivi des loyers et charges
					</p>
					<a href="/pricing">
						<Button size="lg" class="w-full bg-blue-600 text-white hover:bg-blue-700">
							D&eacute;couvrir les offres
							<ArrowRight class="ml-2 h-4 w-4" />
						</Button>
					</a>
				</div>
			</div>
		</div>
	</section>

	<!-- Disclaimer -->
	<section class="pb-12">
		<div class="mx-auto max-w-4xl px-4 sm:px-6">
			<p class="text-center text-xs text-slate-400 dark:text-slate-500">
				Dates indicatives pour l'ann&eacute;e 2026. Les dates exactes peuvent varier selon votre
				situation (zone g&eacute;ographique, r&eacute;gime fiscal, date de cl&ocirc;ture).
				V&eacute;rifiez sur
				<a
					href="https://www.impots.gouv.fr"
					target="_blank"
					rel="noopener noreferrer"
					class="underline hover:text-slate-600 dark:hover:text-slate-400">impots.gouv.fr</a
				>. Ce calendrier ne constitue pas un conseil fiscal.
			</p>
		</div>
	</section>
</main>
