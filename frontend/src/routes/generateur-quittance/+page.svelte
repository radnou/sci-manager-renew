<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import EmailCapture from '$lib/components/EmailCapture.svelte';
	import { ArrowRight, FileText, Download, ChevronDown, CheckCircle } from 'lucide-svelte';
	import { trackEvent, EVENTS } from '$lib/analytics';

	// Form state
	let nomProprietaire = $state('');
	let adresseBien = $state('');
	let nomLocataire = $state('');
	let mois = $state(new Date().getMonth() + 1);
	let annee = $state(new Date().getFullYear());
	let loyerHC = $state(0);
	let charges = $state(0);
	let montantPaye = $state(0);
	let datePaiement = $state(new Date().toISOString().split('T')[0]);
	let modePaiement = $state('virement');

	// Derived
	const totalDu = $derived(loyerHC + charges);
	const periode = $derived(
		`${['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'][mois - 1]} ${annee}`
	);
	const isFormValid = $derived(
		nomProprietaire.length >= 2 &&
			adresseBien.length >= 4 &&
			nomLocataire.length >= 2 &&
			loyerHC > 0 &&
			montantPaye > 0
	);

	// Download state
	let downloading = $state(false);
	let downloaded = $state(false);

	// Email gate: download blocked until email captured
	let emailUnlocked = $state(false);

	// FAQ state
	let openFaq = $state<number | null>(null);

	// Currency formatter
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('fr-FR', {
			style: 'currency',
			currency: 'EUR',
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		}).format(value);
	}

	// Handle numeric input
	function handleInput(setter: (v: number) => void) {
		return (e: Event) => {
			const target = e.target as HTMLInputElement;
			const raw = target.value.replace(/[^0-9.,]/g, '').replace(',', '.');
			const parsed = parseFloat(raw);
			setter(isNaN(parsed) ? 0 : parsed);
		};
	}

	function formatDateFr(dateStr: string): string {
		const d = new Date(dateStr);
		return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
	}

	const modePaiementOptions = [
		{ value: 'virement', label: 'Virement bancaire' },
		{ value: 'cheque', label: 'Chèque' },
		{ value: 'especes', label: 'Espèces' },
		{ value: 'prelevement', label: 'Prélèvement automatique' }
	];

	const faqs = [
		{
			question: 'La quittance est-elle conforme ?',
			answer:
				'Oui. Cette quittance est conforme aux articles 21 et 22 de la loi n\u00B0 89-462 du 6 juillet 1989. Elle mentionne le nom du locataire, la période, le loyer, les charges et le montant total.'
		},
		{
			question: 'Dois-je fournir une quittance ?',
			answer:
				'Oui. Le bailleur est tenu de remettre gratuitement une quittance au locataire qui en fait la demande (article 21 de la loi du 6 juillet 1989). Ce document est indispensable pour le locataire comme justificatif de domicile.'
		},
		{
			question: 'Puis-je automatiser mes quittances ?',
			answer:
				'Oui. Avec GérerSCI, les quittances sont générées automatiquement chaque mois à partir de vos loyers et charges réels. Plus besoin de ressaisir les informations manuellement.'
		}
	];

	async function downloadPDF() {
		if (!isFormValid) return;
		downloading = true;
		try {
			const res = await fetch(
				`${import.meta.env.VITE_API_URL || ''}/api/v1/quitus/public-generate`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						nom_proprietaire: nomProprietaire,
						adresse_bien: adresseBien,
						nom_locataire: nomLocataire,
						periode,
						loyer_hc: loyerHC,
						charges_locatives: charges,
						montant_paye: montantPaye,
						date_paiement: datePaiement,
						mode_paiement: modePaiement
					})
				}
			);
			if (!res.ok) throw new Error('Erreur lors de la génération');
			const blob = await res.blob();
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `quittance-${periode.replace(/\s+/g, '-').toLowerCase()}.pdf`;
			a.click();
			URL.revokeObjectURL(url);
			downloaded = true;
			trackEvent(EVENTS.QUITTANCE_GENERATE, { source: 'public' });
		} catch {
			alert('Erreur lors de la génération du PDF. Veuillez réessayer.');
		} finally {
			downloading = false;
		}
	}

	function toggleFaq(index: number) {
		openFaq = openFaq === index ? null : index;
	}
</script>

<svelte:head>
	<title>Générateur de quittance de loyer gratuit — GérerSCI</title>
	<meta
		name="description"
		content="Générez gratuitement une quittance de loyer conforme en PDF. Modèle gratuit, sans inscription, en 30 secondes. Outil pour propriétaires et SCI."
	/>
	<meta
		name="keywords"
		content="quittance de loyer, modèle gratuit, quittance PDF, quittance locataire, propriétaire, SCI"
	/>
	<link rel="canonical" href="https://gerersci.fr/generateur-quittance" />
	<meta property="og:title" content="Générateur de quittance de loyer gratuit — GérerSCI" />
	<meta
		property="og:description"
		content="Créez une quittance de loyer PDF conforme gratuitement. Sans inscription, résultat immédiat."
	/>
	<meta property="og:url" content="https://gerersci.fr/generateur-quittance" />
	<meta property="og:type" content="website" />
</svelte:head>

<main class="min-h-screen bg-slate-50 dark:bg-slate-950">
	<!-- Hero -->
	<section class="relative overflow-hidden bg-white py-16 sm:py-20 dark:bg-slate-900">
		<div
			class="pointer-events-none absolute inset-0 bg-gradient-to-br from-blue-50/80 via-transparent to-cyan-50/60 dark:from-blue-950/30 dark:to-cyan-950/20"
		></div>
		<div class="relative mx-auto max-w-4xl px-4 text-center sm:px-6">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">
				Outil gratuit
			</Badge>
			<h1
				class="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl dark:text-white"
			>
				Générez votre
				<span class="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
					quittance de loyer
				</span>
				en 30 secondes
			</h1>
			<p class="mt-4 text-lg text-slate-600 dark:text-slate-400">
				Conforme, professionnelle, téléchargeable en PDF. Gratuit et sans inscription.
			</p>
		</div>
	</section>

	<!-- Generator -->
	<section class="py-12 sm:py-16">
		<div class="mx-auto max-w-6xl px-4 sm:px-6">
			<div class="grid gap-8 lg:grid-cols-5">
				<!-- Left: Form (3/5) -->
				<div class="lg:col-span-3">
					<div
						class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 dark:border-slate-700 dark:bg-slate-800"
					>
						<h2 class="mb-6 text-xl font-bold text-slate-900 dark:text-slate-100">
							Informations de la quittance
						</h2>

						<!-- Nom propriétaire / SCI -->
						<div class="mb-6">
							<label
								for="nom-proprietaire"
								class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
							>
								Nom du bailleur (propriétaire ou SCI) <span class="text-rose-500">*</span>
							</label>
							<input
								id="nom-proprietaire"
								type="text"
								bind:value={nomProprietaire}
								placeholder="SCI Belleville"
								class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
							/>
						</div>

						<!-- Adresse du bien -->
						<div class="mb-6">
							<label
								for="adresse-bien"
								class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
							>
								Adresse du bien loué <span class="text-rose-500">*</span>
							</label>
							<input
								id="adresse-bien"
								type="text"
								bind:value={adresseBien}
								placeholder="12 rue de Belleville, 75020 Paris"
								class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
							/>
						</div>

						<!-- Nom locataire -->
						<div class="mb-6">
							<label
								for="nom-locataire"
								class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
							>
								Nom du locataire <span class="text-rose-500">*</span>
							</label>
							<input
								id="nom-locataire"
								type="text"
								bind:value={nomLocataire}
								placeholder="Jean Dupont"
								class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
							/>
						</div>

						<!-- Période -->
						<div class="mb-6">
							<span class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
								Période <span class="text-rose-500">*</span>
							</span>
							<div class="flex gap-3">
								<select
									bind:value={mois}
									aria-label="Mois"
									class="h-12 flex-1 rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:focus:border-blue-400"
								>
									<option value={1}>Janvier</option>
									<option value={2}>Février</option>
									<option value={3}>Mars</option>
									<option value={4}>Avril</option>
									<option value={5}>Mai</option>
									<option value={6}>Juin</option>
									<option value={7}>Juillet</option>
									<option value={8}>Août</option>
									<option value={9}>Septembre</option>
									<option value={10}>Octobre</option>
									<option value={11}>Novembre</option>
									<option value={12}>Décembre</option>
								</select>
								<select
									bind:value={annee}
									aria-label="Année"
									class="h-12 w-32 rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:focus:border-blue-400"
								>
									{#each Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i) as y}
										<option value={y}>{y}</option>
									{/each}
								</select>
							</div>
						</div>

						<!-- Loyer HC -->
						<div class="mb-6">
							<label
								for="loyer-hc"
								class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
							>
								Montant du loyer hors charges <span class="text-rose-500">*</span>
							</label>
							<div class="relative">
								<input
									id="loyer-hc"
									type="text"
									inputmode="decimal"
									value={loyerHC === 0 ? '' : loyerHC.toLocaleString('fr-FR')}
									oninput={handleInput((v) => (loyerHC = v))}
									placeholder="850"
									class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
								/>
								<span
									class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
								>
									&euro;
								</span>
							</div>
						</div>

						<!-- Charges -->
						<div class="mb-6">
							<label
								for="charges"
								class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
							>
								Montant des charges (provisions)
							</label>
							<div class="relative">
								<input
									id="charges"
									type="text"
									inputmode="decimal"
									value={charges === 0 ? '' : charges.toLocaleString('fr-FR')}
									oninput={handleInput((v) => (charges = v))}
									placeholder="150"
									class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
								/>
								<span
									class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
								>
									&euro;
								</span>
							</div>
						</div>

						<!-- Montant payé -->
						<div class="mb-6">
							<label
								for="montant-paye"
								class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
							>
								Montant total payé par le locataire <span class="text-rose-500">*</span>
							</label>
							<div class="relative">
								<input
									id="montant-paye"
									type="text"
									inputmode="decimal"
									value={montantPaye === 0 ? '' : montantPaye.toLocaleString('fr-FR')}
									oninput={handleInput((v) => (montantPaye = v))}
									placeholder="1000"
									class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pr-10 text-base font-medium text-slate-900 shadow-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-400"
								/>
								<span
									class="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400"
								>
									&euro;
								</span>
							</div>
						</div>

						<!-- Date paiement -->
						<div class="mb-6">
							<label
								for="date-paiement"
								class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
							>
								Date de paiement <span class="text-rose-500">*</span>
							</label>
							<input
								id="date-paiement"
								type="date"
								bind:value={datePaiement}
								class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:focus:border-blue-400"
							/>
						</div>

						<!-- Mode de paiement -->
						<div class="mb-6">
							<label
								for="mode-paiement"
								class="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300"
							>
								Mode de paiement
							</label>
							<select
								id="mode-paiement"
								bind:value={modePaiement}
								class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:focus:border-blue-400"
							>
								{#each modePaiementOptions as opt}
									<option value={opt.value}>{opt.label}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>

				<!-- Right: Preview + CTA (2/5) -->
				<div class="lg:col-span-2">
					<div
						class="sticky top-24 rounded-2xl border border-slate-200 bg-white p-6 shadow-lg sm:p-8 dark:border-slate-700 dark:bg-slate-800"
					>
						<div class="mb-6 flex items-center gap-3">
							<div
								class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900/30"
							>
								<FileText class="h-5 w-5 text-blue-600 dark:text-blue-400" />
							</div>
							<h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">
								Aperçu de la quittance
							</h2>
						</div>

						<!-- Preview card mimicking PDF -->
						<div
							class="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900"
						>
							<!-- Header -->
							<div class="mb-4 rounded-lg bg-slate-800 p-3 text-white dark:bg-slate-700">
								<p class="text-sm font-bold">
									{nomProprietaire || 'Nom du bailleur'}
								</p>
								<p class="mt-1 text-xs text-slate-300">QUITTANCE DE LOYER</p>
							</div>

							<!-- Info -->
							<div class="mb-4 space-y-2 text-sm">
								<div class="flex justify-between">
									<span class="text-slate-500 dark:text-slate-400">Locataire</span>
									<span class="font-medium text-slate-900 dark:text-slate-100">
										{nomLocataire || '\u2014'}
									</span>
								</div>
								<div class="flex justify-between">
									<span class="text-slate-500 dark:text-slate-400">Bien</span>
									<span
										class="max-w-[180px] truncate text-right font-medium text-slate-900 dark:text-slate-100"
									>
										{adresseBien || '\u2014'}
									</span>
								</div>
								<div class="flex justify-between">
									<span class="text-slate-500 dark:text-slate-400">Période</span>
									<span class="font-medium text-slate-900 dark:text-slate-100">{periode}</span>
								</div>
							</div>

							<!-- Financial breakdown -->
							<div
								class="mb-4 space-y-2 border-t border-slate-200 pt-3 text-sm dark:border-slate-700"
							>
								<div class="flex justify-between">
									<span class="text-slate-600 dark:text-slate-400">Loyer HC</span>
									<span class="font-medium text-slate-900 dark:text-slate-100">
										{formatCurrency(loyerHC)}
									</span>
								</div>
								<div class="flex justify-between">
									<span class="text-slate-600 dark:text-slate-400">Charges</span>
									<span class="font-medium text-slate-900 dark:text-slate-100">
										{formatCurrency(charges)}
									</span>
								</div>
								<div
									class="flex justify-between border-t border-slate-200 pt-2 dark:border-slate-700"
								>
									<span class="font-semibold text-slate-700 dark:text-slate-300">Total dû</span>
									<span class="font-bold text-slate-900 dark:text-slate-100">
										{formatCurrency(totalDu)}
									</span>
								</div>
								<div class="flex justify-between">
									<span class="font-semibold text-slate-700 dark:text-slate-300">Total payé</span
									>
									<span
										class="font-bold {montantPaye >= totalDu
											? 'text-emerald-600 dark:text-emerald-400'
											: 'text-rose-600 dark:text-rose-400'}"
									>
										{formatCurrency(montantPaye)}
									</span>
								</div>
							</div>

							<!-- Date + mode -->
							<div class="flex justify-between text-xs text-slate-400 dark:text-slate-500">
								<span>
									{modePaiementOptions.find((o) => o.value === modePaiement)?.label || ''}
								</span>
								<span>Payé le {datePaiement ? formatDateFr(datePaiement) : '\u2014'}</span>
							</div>
						</div>

						<!-- Email gate + Download -->
						{#if emailUnlocked}
							<Button
								size="lg"
								class="mb-4 w-full bg-blue-600 text-white hover:bg-blue-700"
								disabled={!isFormValid || downloading}
								onclick={downloadPDF}
							>
								{#if downloading}
									Génération...
								{:else}
									<Download class="mr-2 h-4 w-4" aria-hidden="true" />
									Télécharger la quittance PDF
								{/if}
							</Button>
						{:else}
							<EmailCapture
								source="generateur-quittance"
								title="Téléchargez votre quittance PDF"
								description="Entrez votre email pour débloquer le téléchargement."
								buttonText="Débloquer le PDF"
								context={{
									periode,
									nom_proprietaire: nomProprietaire,
									nom_locataire: nomLocataire,
									montant: formatCurrency(montantPaye)
								}}
								onCaptured={() => (emailUnlocked = true)}
							/>
						{/if}

						<!-- Product bridge (after download) -->
						{#if downloaded}
							<div
								class="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-5 dark:border-emerald-800 dark:bg-emerald-950/30"
							>
								<div class="mb-3 flex items-center gap-2">
									<CheckCircle class="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
									<p class="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
										Votre quittance est prête !
									</p>
								</div>
								<p class="mb-4 text-sm text-emerald-700 dark:text-emerald-300">
									Avec GérerSCI, les quittances sont générées automatiquement
									à partir de vos loyers réels. Plus de saisie manuelle.
								</p>
								<div class="flex flex-col gap-2 sm:flex-row">
									<a
										href="/pricing"
										class="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700"
									>
										Découvrir GérerSCI
										<ArrowRight class="h-4 w-4" />
									</a>
									<a
										href="/#comment-ca-marche"
										class="inline-flex items-center justify-center gap-2 rounded-lg border border-emerald-300 bg-white px-4 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-100 dark:border-emerald-700 dark:bg-emerald-900 dark:text-emerald-300 dark:hover:bg-emerald-800"
									>
										Voir la démonstration
									</a>
								</div>
							</div>
						{/if}

						<!-- CTA -->
						<div
							class="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-5 text-center dark:border-slate-700 dark:bg-slate-900"
						>
							<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">
								Pour générer vos quittances automatiquement chaque mois
							</p>
							<a href="/pricing">
								<Button size="lg" class="w-full bg-blue-600 text-white hover:bg-blue-700">
									Démarrer à 19&euro;/mois
									<ArrowRight class="ml-2 h-4 w-4" />
								</Button>
							</a>
							<p class="mt-2 text-xs text-slate-400 dark:text-slate-500">
								Garanti 30 jours satisfait ou remboursé
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- FAQ -->
	<section class="py-12 sm:py-16">
		<div class="mx-auto max-w-3xl px-4 sm:px-6">
			<h2 class="mb-8 text-center text-2xl font-bold text-slate-900 dark:text-white">
				Questions fréquentes
			</h2>
			<div class="space-y-3">
				{#each faqs as faq, i}
					<div
						class="rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800"
					>
						<button
							class="flex w-full items-center justify-between px-6 py-4 text-left"
							onclick={() => toggleFaq(i)}
							aria-expanded={openFaq === i}
						>
							<span class="text-sm font-semibold text-slate-900 dark:text-slate-100">
								{faq.question}
							</span>
							<ChevronDown
								class="h-5 w-5 shrink-0 text-slate-400 transition-transform duration-200 {openFaq === i ? 'rotate-180' : ''}"
							/>
						</button>
						{#if openFaq === i}
							<div class="border-t border-slate-100 px-6 pb-4 pt-3 dark:border-slate-700">
								<p class="text-sm leading-relaxed text-slate-600 dark:text-slate-400">
									{faq.answer}
									{#if i === 2}
										<a
											href="/pricing"
											class="ml-1 font-medium text-blue-600 underline hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
										>
											Découvrir GérerSCI
										</a>
									{/if}
								</p>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- Disclaimer -->
	<section class="pb-12">
		<div class="mx-auto max-w-6xl px-4 sm:px-6">
			<p class="text-center text-xs text-slate-400 dark:text-slate-500">
				Cette quittance est générée à titre indicatif conformément à l'article 21 de la loi
				n° 89-462 du 6 juillet 1989 et à l'article 1366 du Code civil. Le bailleur est tenu de
				transmettre gratuitement la quittance au locataire qui en fait la demande. Ce document ne
				constitue pas un conseil juridique.
			</p>
		</div>
	</section>
</main>
