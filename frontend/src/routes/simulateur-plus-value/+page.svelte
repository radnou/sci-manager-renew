<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import EmailCapture from '$lib/components/EmailCapture.svelte';
	import { trackEvent, EVENTS } from '$lib/analytics';
	import { ArrowRight, Calculator, TrendingUp, TrendingDown, Info, Clock, Lock } from 'lucide-svelte';

	// --- Form state ---
	let dateAcquisition = $state('');
	let prixAcquisition = $state(0);
	let fraisMode = $state<'pourcentage' | 'montant'>('pourcentage');
	let fraisPourcentage = $state(7.5);
	let fraisMontant = $state(0);
	let travauxMode = $state<'montant' | 'forfait'>('montant');
	let travauxMontant = $state(0);
	let dateCession = $state(new Date().toISOString().split('T')[0]);
	let prixCession = $state(0);

	// --- Derived calculations ---

	const fraisAcquisition = $derived(
		fraisMode === 'pourcentage'
			? Math.round(prixAcquisition * (fraisPourcentage / 100))
			: fraisMontant
	);

	const dureeDetention = $derived.by(() => {
		if (!dateAcquisition || !dateCession) return 0;
		const acq = new Date(dateAcquisition);
		const ces = new Date(dateCession);
		const diffMs = ces.getTime() - acq.getTime();
		if (diffMs <= 0) return 0;
		// Calculate full years of ownership
		let years = ces.getFullYear() - acq.getFullYear();
		const monthDiff = ces.getMonth() - acq.getMonth();
		if (monthDiff < 0 || (monthDiff === 0 && ces.getDate() < acq.getDate())) {
			years--;
		}
		return Math.max(0, years);
	});

	// Forfait travaux 15% if held > 5 years
	const forfaitTravauxEligible = $derived(dureeDetention > 5);
	const forfaitTravaux = $derived(
		forfaitTravauxEligible ? Math.round(prixAcquisition * 0.15) : 0
	);

	const travaux = $derived(
		travauxMode === 'forfait' && forfaitTravauxEligible ? forfaitTravaux : travauxMontant
	);

	const prixAcquisitionMajore = $derived(prixAcquisition + fraisAcquisition + travaux);
	const plusValueBrute = $derived(prixCession - prixAcquisitionMajore);

	// --- Abattement IR (19%) ---
	// 0-5 years: 0%
	// 6th to 21st year: 6% per year (16 years = 96%)
	// 22nd year: 4% → total = 100%
	// Beyond 22 years: exoneration
	function calculateAbattementIR(annees: number): number {
		if (annees <= 5) return 0;
		if (annees >= 22) return 1;
		// Years 6 to 21: 6% per year of ownership beyond 5th
		const anneesAbattement = Math.min(annees - 5, 16);
		let abattement = anneesAbattement * 0.06;
		// 22nd year adds 4%
		if (annees >= 22) {
			abattement += 0.04;
		}
		return Math.min(abattement, 1);
	}

	// --- Abattement PS (17.2%) ---
	// 0-5 years: 0%
	// 6th to 21st year: 1.65% per year
	// 22nd year: 1.60%
	// 23rd to 30th year: 9% per year
	// Beyond 30 years: exoneration
	function calculateAbattementPS(annees: number): number {
		if (annees <= 5) return 0;
		if (annees >= 30) return 1;
		let abattement = 0;
		// Years 6 to 21: 1.65% per year
		const tranche1 = Math.min(Math.max(annees - 5, 0), 16);
		abattement += tranche1 * 0.0165;
		// 22nd year: 1.60%
		if (annees >= 22) {
			abattement += 0.016;
		}
		// Years 23 to 30: 9% per year
		if (annees >= 23) {
			const tranche3 = Math.min(annees - 22, 8);
			abattement += tranche3 * 0.09;
		}
		return Math.min(abattement, 1);
	}

	const abattementIR = $derived(calculateAbattementIR(dureeDetention));
	const abattementPS = $derived(calculateAbattementPS(dureeDetention));

	const pvNetteIR = $derived(Math.max(0, plusValueBrute * (1 - abattementIR)));
	const pvNettePS = $derived(Math.max(0, plusValueBrute * (1 - abattementPS)));

	const impotIR = $derived(pvNetteIR * 0.19);
	const impotPS = $derived(pvNettePS * 0.172);

	// --- Surtaxe (taxe sur les plus-values elevees) ---
	// Applied when PV nette IR > 50 000 EUR
	function calculateSurtaxe(pvNette: number): number {
		if (pvNette <= 50000) return 0;
		if (pvNette <= 60000) return pvNette * 0.02;
		if (pvNette <= 100000) return pvNette * 0.02;
		if (pvNette <= 110000) return pvNette * 0.03;
		if (pvNette <= 150000) return pvNette * 0.03;
		if (pvNette <= 160000) return pvNette * 0.04;
		if (pvNette <= 200000) return pvNette * 0.04;
		if (pvNette <= 210000) return pvNette * 0.05;
		if (pvNette <= 250000) return pvNette * 0.05;
		if (pvNette <= 260000) return pvNette * 0.06;
		return pvNette * 0.06;
	}

	const surtaxe = $derived(calculateSurtaxe(pvNetteIR));
	const totalImpot = $derived(plusValueBrute > 0 ? impotIR + impotPS + surtaxe : 0);
	const netVendeur = $derived(prixCession - totalImpot);

	// Years until full IR / PS exoneration
	const anneesRestantesIR = $derived(Math.max(0, 22 - dureeDetention));
	const anneesRestantesPS = $derived(Math.max(0, 30 - dureeDetention));

	// Has valid inputs
	const hasInputs = $derived(prixAcquisition > 0 && prixCession > 0 && dateAcquisition !== '');

	// Currency formatter
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('fr-FR', {
			style: 'currency',
			currency: 'EUR',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(value);
	}

	function formatPercent(value: number): string {
		return new Intl.NumberFormat('fr-FR', {
			style: 'percent',
			minimumFractionDigits: 1,
			maximumFractionDigits: 1
		}).format(value);
	}

	// Handle currency input
	function handleInput(setter: (v: number) => void) {
		return (e: Event) => {
			const target = e.target as HTMLInputElement;
			const raw = target.value.replace(/[^0-9]/g, '');
			setter(raw ? parseInt(raw, 10) : 0);
		};
	}

	// Email gate for detailed breakdown
	let emailUnlocked = $state(false);

	// Result animation
	let resultChanged = $state(false);
	let resultTimeout: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		void totalImpot;
		resultChanged = true;
		clearTimeout(resultTimeout);
		resultTimeout = setTimeout(() => {
			resultChanged = false;
		}, 300);
	});

	// Abattement timeline data
	const timelineYears = $derived.by(() => {
		const points: Array<{ year: number; ir: number; ps: number }> = [];
		for (let y = 0; y <= 30; y += 1) {
			points.push({
				year: y,
				ir: calculateAbattementIR(y),
				ps: calculateAbattementPS(y)
			});
		}
		return points;
	});
</script>

<svelte:head>
	<title>Simulateur Plus-Value Immobilière Gratuit — GérerSCI</title>
	<meta
		name="description"
		content="Calculez gratuitement l'impôt sur la plus-value immobilière de votre SCI. Abattements IR, prélèvements sociaux, surtaxe et net vendeur."
	/>
	<link rel="canonical" href="https://gerersci.fr/simulateur-plus-value" />
	<meta property="og:url" content="https://gerersci.fr/simulateur-plus-value" />
	<meta property="og:title" content="Simulateur Plus-Value Immobilière Gratuit — GérerSCI" />
	<meta
		property="og:description"
		content="Calculez gratuitement l'impôt sur la plus-value immobilière. Abattements, surtaxe, net vendeur."
	/>
</svelte:head>

<main class="min-h-screen bg-slate-50 dark:bg-slate-950">
	<!-- Header -->
	<section class="relative overflow-hidden bg-white py-16 sm:py-20 dark:bg-slate-900">
		<div
			class="pointer-events-none absolute inset-0 bg-gradient-to-br from-emerald-50/80 via-transparent to-cyan-50/60 dark:from-emerald-950/30 dark:to-cyan-950/20"
		></div>
		<div class="relative mx-auto max-w-4xl px-4 text-center sm:px-6">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">
				Gratuit &middot; Sans inscription
			</Badge>
			<h1
				class="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl dark:text-white"
			>
				Simulateur
				<span
					class="bg-gradient-to-r from-emerald-600 to-cyan-600 bg-clip-text text-transparent"
				>
					Plus-Value Immobilière
				</span>
			</h1>
			<p class="mt-4 text-lg text-slate-600 dark:text-slate-400">
				Estimez l'impôt sur la plus-value lors de la vente d'un bien immobilier.
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
							Informations de la transaction
						</h2>

						<!-- Section: Acquisition -->
						<div class="mb-8">
							<h3
								class="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
							>
								<span
									class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400"
									>1</span
								>
								Acquisition
							</h3>

							<!-- Date d'acquisition -->
							<div class="mb-5">
								<label
									for="date-acquisition"
									class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
								>
									Date d'acquisition <span class="font-normal text-slate-500 dark:text-slate-400">(jj/mm/aaaa)</span>
								</label>
								<input
									id="date-acquisition"
									type="date"
									lang="fr-FR"
									bind:value={dateAcquisition}
									max={dateCession}
									aria-describedby="date-acquisition-hint"
									class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:focus:border-emerald-400"
								/>
								<p id="date-acquisition-hint" class="mt-1 text-xs text-slate-500 dark:text-slate-400">
									Format français : jour / mois / année (ex : 15/03/2010).
								</p>
							</div>

							<!-- Prix d'acquisition -->
							<div class="mb-5">
								<label
									for="prix-acquisition"
									class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
								>
									Prix d'acquisition
								</label>
								<div class="relative">
									<input
										id="prix-acquisition"
										type="text"
										inputmode="numeric"
										value={prixAcquisition === 0
											? ''
											: prixAcquisition.toLocaleString('fr-FR')}
										oninput={handleInput((v) => (prixAcquisition = v))}
										placeholder="0"
										class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-emerald-400"
									/>
									<span
										class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
									>
										&euro;
									</span>
								</div>
							</div>

							<!-- Frais d'acquisition -->
							<div class="mb-5">
								<label
									for="frais-acquisition"
									class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
								>
									Frais d'acquisition (notaire)
								</label>
								<div class="mb-2">
									<div
										role="radiogroup"
										aria-label="Mode de calcul des frais"
										class="inline-flex items-center rounded-lg bg-slate-100 p-0.5 text-sm dark:bg-slate-700"
									>
										<button
											class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors {fraisMode ===
											'pourcentage'
												? 'bg-emerald-600 text-white shadow-sm'
												: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
											onclick={() => (fraisMode = 'pourcentage')}
										>
											Forfait %
										</button>
										<button
											class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors {fraisMode ===
											'montant'
												? 'bg-emerald-600 text-white shadow-sm'
												: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
											onclick={() => (fraisMode = 'montant')}
										>
											Montant exact
										</button>
									</div>
								</div>
								{#if fraisMode === 'pourcentage'}
									<div class="relative">
										<input
											id="frais-acquisition"
											type="number"
											step="0.1"
											min="0"
											max="100"
											bind:value={fraisPourcentage}
											class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:focus:border-emerald-400"
										/>
										<span
											class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
										>
											%
										</span>
									</div>
									<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
										Forfait 7,5% pour frais de notaire (par défaut)
									</p>
								{:else}
									<div class="relative">
										<input
											id="frais-acquisition"
											type="text"
											inputmode="numeric"
											value={fraisMontant === 0
												? ''
												: fraisMontant.toLocaleString('fr-FR')}
											oninput={handleInput((v) => (fraisMontant = v))}
											placeholder="0"
											class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-emerald-400"
										/>
										<span
											class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
										>
											&euro;
										</span>
									</div>
								{/if}
								{#if prixAcquisition > 0}
									<p class="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
										Frais retenus : {formatCurrency(fraisAcquisition)}
									</p>
								{/if}
							</div>

							<!-- Travaux -->
							<div class="mb-5">
								<label
									for="travaux"
									class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
								>
									Travaux réalisés
								</label>
								<div class="mb-2">
									<div
										role="radiogroup"
										aria-label="Mode de calcul des travaux"
										class="inline-flex items-center rounded-lg bg-slate-100 p-0.5 text-sm dark:bg-slate-700"
									>
										<button
											class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors {travauxMode ===
											'montant'
												? 'bg-emerald-600 text-white shadow-sm'
												: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
											onclick={() => (travauxMode = 'montant')}
										>
											Montant réel
										</button>
										<button
											class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors {travauxMode ===
											'forfait'
												? 'bg-emerald-600 text-white shadow-sm'
												: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
											onclick={() => (travauxMode = 'forfait')}
											disabled={!forfaitTravauxEligible}
											title={forfaitTravauxEligible
												? 'Forfait 15% du prix d\'acquisition'
												: 'Disponible après 5 ans de détention'}
										>
											Forfait 15%
										</button>
									</div>
								</div>
								{#if travauxMode === 'montant'}
									<div class="relative">
										<input
											id="travaux"
											type="text"
											inputmode="numeric"
											value={travauxMontant === 0
												? ''
												: travauxMontant.toLocaleString('fr-FR')}
											oninput={handleInput((v) => (travauxMontant = v))}
											placeholder="0"
											class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-emerald-400"
										/>
										<span
											class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
										>
											&euro;
										</span>
									</div>
									<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
										Montant des travaux justifiés (factures)
									</p>
								{:else if forfaitTravauxEligible}
									<div
										class="rounded-xl border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-800 dark:bg-emerald-900/20"
									>
										<p class="text-sm font-medium text-emerald-700 dark:text-emerald-300">
											Forfait travaux : {formatCurrency(forfaitTravaux)}
										</p>
										<p class="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
											15% du prix d'acquisition (détention &gt; 5 ans)
										</p>
									</div>
								{:else}
									<div
										class="rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-900/20"
									>
										<p class="text-xs text-amber-700 dark:text-amber-300">
											Le forfait 15% n'est disponible qu'après 5 ans de détention.
										</p>
									</div>
								{/if}
							</div>
						</div>

						<!-- Section: Cession -->
						<div>
							<h3
								class="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400"
							>
								<span
									class="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700 dark:bg-blue-900/40 dark:text-blue-400"
									>2</span
								>
								Cession (vente)
							</h3>

							<!-- Date de cession -->
							<div class="mb-5">
								<label
									for="date-cession"
									class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
								>
									Date de cession <span class="font-normal text-slate-500 dark:text-slate-400">(jj/mm/aaaa)</span>
								</label>
								<input
									id="date-cession"
									type="date"
									lang="fr-FR"
									bind:value={dateCession}
									min={dateAcquisition}
									aria-describedby="date-cession-hint"
									class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:focus:border-blue-400"
								/>
								<p id="date-cession-hint" class="mt-1 text-xs text-slate-500 dark:text-slate-400">
									Format français : jour / mois / année (ex : 15/03/2026).
								</p>
							</div>

							<!-- Prix de cession -->
							<div class="mb-5">
								<label
									for="prix-cession"
									class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
								>
									Prix de cession
								</label>
								<div class="relative">
									<input
										id="prix-cession"
										type="text"
										inputmode="numeric"
										value={prixCession === 0
											? ''
											: prixCession.toLocaleString('fr-FR')}
										oninput={handleInput((v) => (prixCession = v))}
										placeholder="0"
										class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
									/>
									<span
										class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
									>
										&euro;
									</span>
								</div>
							</div>
						</div>

						<!-- Duration info -->
						{#if dureeDetention > 0}
							<div
								class="mt-4 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900"
							>
								<Clock class="h-4 w-4 text-slate-500" />
								<span class="text-sm text-slate-600 dark:text-slate-400">
									Durée de détention :
									<strong class="text-slate-900 dark:text-slate-100"
										>{dureeDetention} an{dureeDetention > 1 ? 's' : ''}</strong
									>
								</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Right: Result card (2/5) -->
				<div class="lg:col-span-2">
					<div
						class="sticky top-24 space-y-6"
					>
						<!-- Results card -->
						<div
							class="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg sm:p-8 dark:border-slate-700 dark:bg-slate-800 {resultChanged
								? 'scale-[1.01]'
								: 'scale-100'} transition-transform duration-200"
						>
							<div class="mb-6 flex items-center gap-3">
								<div
									class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-900/30"
								>
									<Calculator class="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
								</div>
								<h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">
									Résultat fiscal
								</h2>
							</div>

							{#if !hasInputs}
								<p class="text-sm text-slate-500 dark:text-slate-400">
									Renseignez les informations de la transaction pour voir le résultat.
								</p>
							{:else}
								<!-- Plus-value brute -->
								<div
									class="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700"
								>
									<span class="text-sm text-slate-600 dark:text-slate-400"
										>Plus-value brute</span
									>
									<span
										class="text-sm font-semibold {plusValueBrute > 0
											? 'text-emerald-600 dark:text-emerald-400'
											: plusValueBrute < 0
												? 'text-rose-600 dark:text-rose-400'
												: 'text-slate-900 dark:text-slate-100'}"
									>
										{formatCurrency(plusValueBrute)}
									</span>
								</div>

								{#if plusValueBrute > 0}
									{#if emailUnlocked}
										<!-- Abattements -->
										<div
											class="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700"
										>
											<span class="text-sm text-slate-600 dark:text-slate-400">
												Abattement IR ({formatPercent(abattementIR)})
											</span>
											<span
												class="text-sm font-semibold text-slate-900 dark:text-slate-100"
											>
												{formatCurrency(pvNetteIR)}
											</span>
										</div>
										<div
											class="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700"
										>
											<span class="text-sm text-slate-600 dark:text-slate-400">
												Abattement PS ({formatPercent(abattementPS)})
											</span>
											<span
												class="text-sm font-semibold text-slate-900 dark:text-slate-100"
											>
												{formatCurrency(pvNettePS)}
											</span>
										</div>

										<!-- Impots details -->
										<div
											class="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700"
										>
											<span class="text-sm text-slate-600 dark:text-slate-400"
												>Impôt IR (19%)</span
											>
											<span
												class="text-sm font-semibold text-rose-600 dark:text-rose-400"
											>
												{formatCurrency(impotIR)}
											</span>
										</div>
										<div
											class="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700"
										>
											<span class="text-sm text-slate-600 dark:text-slate-400"
												>Prélèvements sociaux (17,2%)</span
											>
											<span
												class="text-sm font-semibold text-rose-600 dark:text-rose-400"
											>
												{formatCurrency(impotPS)}
											</span>
										</div>

										{#if surtaxe > 0}
											<div
												class="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700"
											>
												<span class="text-sm text-slate-600 dark:text-slate-400"
													>Surtaxe PV élevées</span
												>
												<span
													class="text-sm font-semibold text-rose-600 dark:text-rose-400"
												>
													{formatCurrency(surtaxe)}
												</span>
											</div>
										{/if}

										<!-- Total impot -->
										<div
											class="mb-4 rounded-xl bg-rose-50 p-4 dark:bg-rose-900/20"
										>
											<div class="flex items-center justify-between">
												<div class="flex items-center gap-2">
													<TrendingDown
														class="h-5 w-5 text-rose-600 dark:text-rose-400"
													/>
													<span
														class="text-sm font-medium text-slate-700 dark:text-slate-300"
														>Total impositions</span
													>
												</div>
												<span
													class="text-xl font-bold text-rose-600 dark:text-rose-400"
												>
													{formatCurrency(totalImpot)}
												</span>
											</div>
										</div>

										<!-- Net vendeur -->
										<div
											class="mb-6 rounded-xl bg-emerald-50 p-4 dark:bg-emerald-900/20"
										>
											<div class="flex items-center justify-between">
												<div class="flex items-center gap-2">
													<TrendingUp
														class="h-5 w-5 text-emerald-600 dark:text-emerald-400"
													/>
													<span
														class="text-sm font-medium text-slate-700 dark:text-slate-300"
														>Net vendeur</span
													>
												</div>
												<span
													class="text-xl font-bold text-emerald-600 dark:text-emerald-400"
												>
													{formatCurrency(netVendeur)}
												</span>
											</div>
										</div>
									{:else}
										<!-- Blurred teaser of detailed breakdown -->
										<div class="relative mb-6">
											<div class="pointer-events-none select-none blur-sm" aria-hidden="true">
												<div
													class="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700"
												>
													<span class="text-sm text-slate-600 dark:text-slate-400">
														Abattement IR ({formatPercent(abattementIR)})
													</span>
													<span class="text-sm font-semibold text-slate-900 dark:text-slate-100">
														{formatCurrency(pvNetteIR)}
													</span>
												</div>
												<div
													class="mb-3 flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-700"
												>
													<span class="text-sm text-slate-600 dark:text-slate-400">
														Abattement PS ({formatPercent(abattementPS)})
													</span>
													<span class="text-sm font-semibold text-slate-900 dark:text-slate-100">
														{formatCurrency(pvNettePS)}
													</span>
												</div>
												<div class="mb-4 rounded-xl bg-rose-50 p-4 dark:bg-rose-900/20">
													<div class="flex items-center justify-between">
														<span class="text-sm font-medium text-slate-700 dark:text-slate-300">Total impositions</span>
														<span class="text-xl font-bold text-rose-600 dark:text-rose-400">{formatCurrency(totalImpot)}</span>
													</div>
												</div>
											</div>
											<!-- Overlay with lock + email capture -->
											<div class="absolute inset-0 flex items-center justify-center">
												<div class="w-full max-w-sm">
													<div class="mb-3 flex items-center justify-center gap-2">
														<Lock class="h-4 w-4 text-slate-500 dark:text-slate-400" />
														<span class="text-sm font-medium text-slate-700 dark:text-slate-300">
															Détail fiscal complet
														</span>
													</div>
													<EmailCapture
														source="simulateur-plus-value"
														title="Recevez le détail de votre imposition"
														description="Abattements, impôt IR, prélèvements sociaux, surtaxe et net vendeur — envoyés à votre email."
														buttonText="Voir le détail"
														onCaptured={() => {
															emailUnlocked = true;
															trackEvent(EVENTS.SIMULATEUR_EMAIL_CAPTURE, { source: 'simulateur-plus-value' });
														}}
													/>
												</div>
											</div>
										</div>
									{/if}
								{:else}
									<!-- Pas de plus-value -->
									<div
										class="mb-6 rounded-xl bg-slate-50 p-4 dark:bg-slate-900/30"
									>
										<p class="text-sm text-slate-600 dark:text-slate-400">
											{#if plusValueBrute < 0}
												Pas de plus-value : la cession entraîne une moins-value
												de {formatCurrency(Math.abs(plusValueBrute))}. Aucun
												impôt n'est dû.
											{:else}
												Pas de plus-value. Aucun impôt n'est dû.
											{/if}
										</p>
									</div>
								{/if}

								<!-- Exoneration info (gated behind email) -->
								{#if emailUnlocked && plusValueBrute > 0 && dureeDetention < 30}
									<div
										class="mb-6 rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20"
									>
										<div class="mb-2 flex items-center gap-2">
											<Info class="h-4 w-4 text-blue-600 dark:text-blue-400" />
											<span
												class="text-sm font-medium text-blue-700 dark:text-blue-300"
											>
												Perspective d'exonération
											</span>
										</div>
										<div class="space-y-1 text-xs text-blue-600 dark:text-blue-400">
											{#if anneesRestantesIR > 0}
												<p>
													Exonération IR dans <strong
														>{anneesRestantesIR} an{anneesRestantesIR > 1
															? 's'
															: ''}</strong
													> (22 ans de détention)
												</p>
											{:else}
												<p>IR : exonération totale atteinte</p>
											{/if}
											{#if anneesRestantesPS > 0}
												<p>
													Exonération PS dans <strong
														>{anneesRestantesPS} an{anneesRestantesPS > 1
															? 's'
															: ''}</strong
													> (30 ans de détention)
												</p>
											{:else}
												<p>Prélèvements sociaux : exonération totale atteinte</p>
											{/if}
										</div>
									</div>
								{:else if emailUnlocked && plusValueBrute > 0 && dureeDetention >= 30}
									<div
										class="mb-6 rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-900/20"
									>
										<div class="flex items-center gap-2">
											<TrendingUp
												class="h-4 w-4 text-emerald-600 dark:text-emerald-400"
											/>
											<span
												class="text-sm font-medium text-emerald-700 dark:text-emerald-300"
											>
												Exonération totale atteinte (30 ans)
											</span>
										</div>
									</div>
								{/if}

								<!-- CTA -->
								<div
									class="rounded-xl border border-slate-200 bg-slate-50 p-5 text-center dark:border-slate-700 dark:bg-slate-900"
								>
									<p
										class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300"
									>
										Gérez votre patrimoine SCI en toute simplicité
									</p>
									<a href="/register">
										<Button
											size="lg"
											class="w-full bg-emerald-600 text-white hover:bg-emerald-700"
										>
											Créer mon compte gratuit
											<ArrowRight class="ml-2 h-4 w-4" />
										</Button>
									</a>
								</div>
							{/if}
						</div>

						<!-- Abattement timeline (gated behind email) -->
						{#if emailUnlocked && hasInputs && plusValueBrute > 0}
							<div
								class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800"
							>
								<h3
									class="mb-4 text-sm font-bold text-slate-900 dark:text-slate-100"
								>
									Abattements selon la durée de détention
								</h3>

								<!-- Visual timeline bar chart -->
								<div class="space-y-4">
									<!-- IR bar -->
									<div>
										<div
											class="mb-1 flex items-center justify-between text-xs"
										>
											<span class="font-medium text-blue-600 dark:text-blue-400"
												>IR (19%)</span
											>
											<span class="text-slate-500"
												>Exonération à 22 ans</span
											>
										</div>
										<div
											class="relative h-5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700"
										>
											<div
												class="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-500"
												style="width: {Math.min(
													(dureeDetention / 22) * 100,
													100
												)}%"
											></div>
											{#if dureeDetention > 0}
												<span
													class="absolute inset-0 flex items-center justify-center text-[10px] font-bold {dureeDetention >=
													11
														? 'text-white'
														: 'text-slate-600 dark:text-slate-300'}"
												>
													{formatPercent(abattementIR)}
												</span>
											{/if}
										</div>
									</div>

									<!-- PS bar -->
									<div>
										<div
											class="mb-1 flex items-center justify-between text-xs"
										>
											<span
												class="font-medium text-emerald-600 dark:text-emerald-400"
												>PS (17,2%)</span
											>
											<span class="text-slate-500"
												>Exonération à 30 ans</span
											>
										</div>
										<div
											class="relative h-5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700"
										>
											<div
												class="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500"
												style="width: {Math.min(
													(dureeDetention / 30) * 100,
													100
												)}%"
											></div>
											{#if dureeDetention > 0}
												<span
													class="absolute inset-0 flex items-center justify-center text-[10px] font-bold {dureeDetention >=
													15
														? 'text-white'
														: 'text-slate-600 dark:text-slate-300'}"
												>
													{formatPercent(abattementPS)}
												</span>
											{/if}
										</div>
									</div>

									<!-- Year marker -->
									<div class="flex justify-between text-[10px] text-slate-400">
										<span>0 an</span>
										<span>5</span>
										<span>10</span>
										<span>15</span>
										<span>22</span>
										<span>30 ans</span>
									</div>
								</div>

								<!-- Current position marker -->
								{#if dureeDetention > 0 && dureeDetention < 30}
									<div class="mt-3 text-center">
										<span
											class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-slate-700 dark:text-slate-300"
										>
											<Clock class="h-3 w-3" />
											Vous êtes à {dureeDetention} an{dureeDetention > 1
												? 's'
												: ''}
										</span>
									</div>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- Disclaimer -->
	<section class="pb-12">
		<div class="mx-auto max-w-6xl px-4 sm:px-6">
			<p class="text-center text-xs text-slate-400 dark:text-slate-500">
				Simulation indicative. Les résultats ne constituent pas un conseil fiscal ou
				juridique. Consultez votre notaire pour votre situation exacte.
			</p>
		</div>
	</section>
</main>
