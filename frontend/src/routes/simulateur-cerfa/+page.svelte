<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { ArrowRight, Calculator, TrendingDown, TrendingUp, Info } from 'lucide-svelte';

	// Form state
	let loyersAnnuels = $state(0);
	let chargesDeductibles = $state(0);
	let interetsEmprunt = $state(0);
	let travaux = $state(0);
	let regime = $state<'reel' | 'micro'>('reel');

	// Micro-foncier (abattement 30%)
	const microFoncier = $derived(loyersAnnuels * 0.7);

	// Regime reel
	const totalCharges = $derived(chargesDeductibles + interetsEmprunt + travaux);
	const resultatReel = $derived(loyersAnnuels - totalCharges);

	// Deficit foncier: plafond 10 700 EUR imputable sur revenu global (hors interets)
	const chargesHorsInterets = $derived(chargesDeductibles + travaux);
	const resultatHorsInterets = $derived(loyersAnnuels - chargesHorsInterets);
	const deficitImputable = $derived(
		resultatReel < 0 ? Math.max(resultatHorsInterets < 0 ? resultatHorsInterets : 0, -10700) : 0
	);

	// Resultat selon regime choisi
	const resultat = $derived(regime === 'micro' ? microFoncier : resultatReel);

	// Economie estimee (TMI 30%)
	const economieEstimee = $derived(
		resultat < 0 ? Math.abs(deficitImputable) * 0.3 : 0
	);

	// Micro-foncier eligibility
	const microEligible = $derived(loyersAnnuels > 0 && loyersAnnuels <= 15000);

	// Comparison micro vs reel (when eligible)
	const differenceRegimes = $derived(microFoncier - resultatReel);

	// Currency formatter
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('fr-FR', {
			style: 'currency',
			currency: 'EUR',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(value);
	}

	// Handle input: parse from locale string
	function handleInput(setter: (v: number) => void) {
		return (e: Event) => {
			const target = e.target as HTMLInputElement;
			const raw = target.value.replace(/[^0-9]/g, '');
			setter(raw ? parseInt(raw, 10) : 0);
		};
	}

	// Track previous resultat for animation
	let resultChanged = $state(false);
	let resultTimeout: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		// Subscribe to resultat changes
		void resultat;
		resultChanged = true;
		clearTimeout(resultTimeout);
		resultTimeout = setTimeout(() => {
			resultChanged = false;
		}, 300);
	});
</script>

<svelte:head>
	<title>Simulateur CERFA 2044 gratuit — GérerSCI</title>
	<meta
		name="description"
		content="Estimez votre déclaration de revenus fonciers 2044 en 3 minutes. Gratuit, sans inscription."
	/>
	<link rel="canonical" href="https://gerersci.fr/simulateur-cerfa" />
</svelte:head>

<main class="min-h-screen bg-slate-50 dark:bg-slate-950">
	<!-- Header -->
	<section class="relative overflow-hidden bg-white py-16 sm:py-20 dark:bg-slate-900">
		<div
			class="pointer-events-none absolute inset-0 bg-gradient-to-br from-blue-50/80 via-transparent to-cyan-50/60 dark:from-blue-950/30 dark:to-cyan-950/20"
		></div>
		<div class="relative mx-auto max-w-4xl px-4 text-center sm:px-6">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">
				Gratuit &middot; Sans inscription
			</Badge>
			<h1
				class="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl dark:text-white"
			>
				Simulateur
				<span class="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
					CERFA 2044
				</span>
			</h1>
			<p class="mt-4 text-lg text-slate-600 dark:text-slate-400">
				Estimez votre déclaration de revenus fonciers en 3 minutes.
			</p>
		</div>
	</section>

	<!-- Simulator -->
	<section class="py-12 sm:py-16">
		<div class="mx-auto max-w-6xl px-4 sm:px-6">
			<div class="grid gap-8 lg:grid-cols-5">
				<!-- Left: Form (3/5) -->
				<div class="lg:col-span-3">
					<div
						class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 dark:border-slate-700 dark:bg-slate-800"
					>
						<h2 class="mb-6 text-xl font-bold text-slate-900 dark:text-slate-100">
							Vos revenus et charges
						</h2>

						<!-- Regime toggle -->
						<div class="mb-8">
							<span id="regime-label" class="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
								Régime fiscal
							</span>
							<div
								role="radiogroup"
								aria-labelledby="regime-label"
								class="inline-flex items-center rounded-xl bg-slate-100 p-1 shadow-sm dark:bg-slate-700"
							>
								<button
									class="rounded-lg px-5 py-2.5 text-sm font-medium transition-colors {regime ===
									'reel'
										? 'bg-blue-600 text-white shadow-sm'
										: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
									onclick={() => (regime = 'reel')}
								>
									Régime réel
								</button>
								<button
									class="rounded-lg px-5 py-2.5 text-sm font-medium transition-colors {regime ===
									'micro'
										? 'bg-blue-600 text-white shadow-sm'
										: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
									onclick={() => (regime = 'micro')}
								>
									Micro-foncier
								</button>
							</div>
							{#if regime === 'micro' && loyersAnnuels > 15000}
								<p class="mt-2 text-sm text-rose-600 dark:text-rose-400">
									Le micro-foncier est réservé aux revenus fonciers &le; 15 000 &euro;/an.
								</p>
							{/if}
						</div>

						<!-- Loyers annuels -->
						<div class="mb-6">
							<label
								for="loyers"
								class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
							>
								Loyers annuels bruts encaissés
							</label>
							<div class="relative">
								<input
									id="loyers"
									type="text"
									inputmode="numeric"
									value={loyersAnnuels === 0 ? '' : loyersAnnuels.toLocaleString('fr-FR')}
									oninput={handleInput((v) => (loyersAnnuels = v))}
									placeholder="0"
									class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
								/>
								<span
									class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
								>
									&euro;
								</span>
							</div>
							<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
								Total des loyers (hors charges) perçus sur l'année
							</p>
						</div>

						{#if regime === 'reel'}
							<!-- Charges deductibles -->
							<div class="mb-6">
								<label
									for="charges"
									class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
								>
									Charges déductibles
								</label>
								<div class="relative">
									<input
										id="charges"
										type="text"
										inputmode="numeric"
										value={chargesDeductibles === 0
											? ''
											: chargesDeductibles.toLocaleString('fr-FR')}
										oninput={handleInput((v) => (chargesDeductibles = v))}
										placeholder="0"
										class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
									/>
									<span
										class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
									>
										&euro;
									</span>
								</div>
								<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
									Copropriété, taxe foncière, assurance PNO, frais de gestion...
								</p>
							</div>

							<!-- Interets emprunt -->
							<div class="mb-6">
								<label
									for="interets"
									class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
								>
									Intérêts d'emprunt
								</label>
								<div class="relative">
									<input
										id="interets"
										type="text"
										inputmode="numeric"
										value={interetsEmprunt === 0
											? ''
											: interetsEmprunt.toLocaleString('fr-FR')}
										oninput={handleInput((v) => (interetsEmprunt = v))}
										placeholder="0"
										class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
									/>
									<span
										class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
									>
										&euro;
									</span>
								</div>
								<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
									Intérêts du prêt immobilier payés sur l'année
								</p>
							</div>

							<!-- Travaux -->
							<div class="mb-6">
								<label
									for="travaux"
									class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
								>
									Travaux déductibles
								</label>
								<div class="relative">
									<input
										id="travaux"
										type="text"
										inputmode="numeric"
										value={travaux === 0 ? '' : travaux.toLocaleString('fr-FR')}
										oninput={handleInput((v) => (travaux = v))}
										placeholder="0"
										class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
									/>
									<span
										class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
									>
										&euro;
									</span>
								</div>
								<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
									Travaux d'entretien, réparation et amélioration
								</p>
							</div>
						{/if}
					</div>
				</div>

				<!-- Right: Result card (2/5) -->
				<div class="lg:col-span-2">
					<div
						class="sticky top-24 rounded-2xl border border-slate-200 bg-white p-6 shadow-lg sm:p-8 dark:border-slate-700 dark:bg-slate-800 {resultChanged ? 'scale-[1.01]' : 'scale-100'} transition-transform duration-200"
					>
						<div class="mb-6 flex items-center gap-3">
							<div
								class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900/30"
							>
								<Calculator class="h-5 w-5 text-blue-600 dark:text-blue-400" />
							</div>
							<h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">
								Résultat fiscal
							</h2>
						</div>

						<!-- Revenus bruts -->
						<div class="mb-4 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700">
							<span class="text-sm text-slate-600 dark:text-slate-400">Revenus fonciers bruts</span>
							<span class="text-sm font-semibold text-slate-900 dark:text-slate-100">
								{formatCurrency(loyersAnnuels)}
							</span>
						</div>

						{#if regime === 'reel'}
							<!-- Total charges -->
							<div class="mb-4 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700">
								<span class="text-sm text-slate-600 dark:text-slate-400">Total charges déductibles</span>
								<span class="text-sm font-semibold text-rose-600 dark:text-rose-400">
									- {formatCurrency(totalCharges)}
								</span>
							</div>
						{:else}
							<!-- Abattement micro -->
							<div class="mb-4 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700">
								<span class="text-sm text-slate-600 dark:text-slate-400">Abattement forfaitaire (30%)</span>
								<span class="text-sm font-semibold text-rose-600 dark:text-rose-400">
									- {formatCurrency(loyersAnnuels * 0.3)}
								</span>
							</div>
						{/if}

						<!-- Resultat fiscal -->
						<div
							class="mb-6 rounded-xl p-4 {resultat >= 0
								? 'bg-emerald-50 dark:bg-emerald-900/20'
								: 'bg-rose-50 dark:bg-rose-900/20'}"
						>
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-2">
									{#if resultat >= 0}
										<TrendingUp class="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
									{:else}
										<TrendingDown class="h-5 w-5 text-rose-600 dark:text-rose-400" />
									{/if}
									<span class="text-sm font-medium text-slate-700 dark:text-slate-300">
										Résultat fiscal {regime === 'micro' ? '(micro)' : '(réel)'}
									</span>
								</div>
								<span
									class="text-xl font-bold {resultat >= 0
										? 'text-emerald-600 dark:text-emerald-400'
										: 'text-rose-600 dark:text-rose-400'}"
								>
									{formatCurrency(resultat)}
								</span>
							</div>
							{#if resultat < 0 && regime === 'reel'}
								<p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
									Déficit foncier imputable sur le revenu global :
									<strong class="text-rose-600 dark:text-rose-400">{formatCurrency(deficitImputable)}</strong>
									(plafond 10 700 &euro;)
								</p>
							{/if}
						</div>

						<!-- Economie estimee -->
						{#if resultat < 0 && regime === 'reel' && economieEstimee > 0}
							<div class="mb-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-900/20">
								<div class="flex items-center justify-between">
									<span class="text-sm font-medium text-emerald-700 dark:text-emerald-300">
										Économie d'impôt estimée
									</span>
									<span class="text-lg font-bold text-emerald-600 dark:text-emerald-400">
										~ {formatCurrency(economieEstimee)}
									</span>
								</div>
								<p class="mt-1 text-xs text-emerald-600/70 dark:text-emerald-400/70">
									Estimation basée sur une TMI de 30%
								</p>
							</div>
						{/if}

						<!-- Comparison micro vs reel (when eligible) -->
						{#if microEligible && regime === 'reel' && loyersAnnuels > 0}
							<div class="mb-6 rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
								<div class="flex items-center gap-2 mb-2">
									<Info class="h-4 w-4 text-blue-600 dark:text-blue-400" />
									<span class="text-sm font-medium text-blue-700 dark:text-blue-300">
										Comparaison micro-foncier
									</span>
								</div>
								<div class="grid grid-cols-2 gap-3 text-sm">
									<div>
										<span class="text-slate-500 dark:text-slate-400">Réel</span>
										<p class="font-semibold text-slate-900 dark:text-slate-100">{formatCurrency(resultatReel)}</p>
									</div>
									<div>
										<span class="text-slate-500 dark:text-slate-400">Micro-foncier</span>
										<p class="font-semibold text-slate-900 dark:text-slate-100">{formatCurrency(microFoncier)}</p>
									</div>
								</div>
								{#if differenceRegimes > 0}
									<p class="mt-2 text-xs text-blue-600 dark:text-blue-400">
										Le régime réel vous fait économiser {formatCurrency(differenceRegimes)} de base imposable.
									</p>
								{:else if differenceRegimes < 0}
									<p class="mt-2 text-xs text-blue-600 dark:text-blue-400">
										Le micro-foncier vous fait économiser {formatCurrency(Math.abs(differenceRegimes))} de base imposable.
									</p>
								{:else}
									<p class="mt-2 text-xs text-blue-600 dark:text-blue-400">
										Les deux régimes donnent le même résultat.
									</p>
								{/if}
							</div>
						{/if}

						{#if microEligible && regime === 'micro' && loyersAnnuels > 0}
							<div class="mb-6 rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
								<div class="flex items-center gap-2 mb-2">
									<Info class="h-4 w-4 text-blue-600 dark:text-blue-400" />
									<span class="text-sm font-medium text-blue-700 dark:text-blue-300">
										Le saviez-vous ?
									</span>
								</div>
								<p class="text-xs text-blue-600 dark:text-blue-400">
									Avec le régime réel, vous pourriez déduire vos charges réelles (travaux, intérêts, copropriété...) et potentiellement réduire davantage votre base imposable.
								</p>
							</div>
						{/if}

						<!-- CTA -->
						<div class="rounded-xl border border-slate-200 bg-slate-50 p-5 text-center dark:border-slate-700 dark:bg-slate-900">
							<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">
								Pour générer votre CERFA 2044 officiel prêt à déposer
							</p>
							<a href="/register">
								<Button
									size="lg"
									class="w-full bg-blue-600 text-white hover:bg-blue-700"
								>
									Créer mon compte gratuit
									<ArrowRight class="ml-2 h-4 w-4" />
								</Button>
							</a>
						</div>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- Disclaimer -->
	<section class="pb-12">
		<div class="mx-auto max-w-6xl px-4 sm:px-6">
			<p class="text-center text-xs text-slate-400 dark:text-slate-500">
				Simulation indicative. Les résultats ne constituent pas un conseil fiscal.
				Consultez votre expert-comptable pour votre déclaration officielle.
			</p>
		</div>
	</section>
</main>
