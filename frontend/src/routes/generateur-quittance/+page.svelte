<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import EmailCapture from '$lib/components/EmailCapture.svelte';
	import { ArrowRight, FileText, Download } from 'lucide-svelte';

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

	// Email gate: download blocked until email captured
	let emailUnlocked = $state(false);

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
						date_paiement: datePaiement
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
		} catch {
			alert('Erreur lors de la génération du PDF. Veuillez réessayer.');
		} finally {
			downloading = false;
		}
	}
</script>

<svelte:head>
	<title>Générateur de quittance de loyer gratuit — GérerSCI</title>
	<meta
		name="description"
		content="Générez gratuitement une quittance de loyer conforme en PDF. Sans inscription, en 2 minutes. Outil gratuit pour propriétaires et SCI."
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
				Générateur de
				<span class="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
					quittance de loyer
				</span>
			</h1>
			<p class="mt-4 text-lg text-slate-600 dark:text-slate-400">
				Créez une quittance de loyer conforme en PDF, gratuitement, en 2 minutes.
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
								Nom du propriétaire ou de la SCI
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
								Adresse du bien loué
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
								Nom du locataire
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
								Période
							</span>
							<div class="flex gap-3">
								<select
									bind:value={mois}
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
								Montant du loyer hors charges
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
								Montant total payé par le locataire
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
								Date de paiement
							</label>
							<input
								id="date-paiement"
								type="date"
								bind:value={datePaiement}
								class="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-base font-medium text-slate-900 shadow-sm outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-600 dark:bg-slate-700 dark:text-white dark:focus:border-blue-400"
							/>
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
									{nomProprietaire || 'Nom du propriétaire / SCI'}
								</p>
								<p class="mt-1 text-xs text-slate-300">QUITTANCE DE LOYER</p>
							</div>

							<!-- Info -->
							<div class="mb-4 space-y-2 text-sm">
								<div class="flex justify-between">
									<span class="text-slate-500 dark:text-slate-400">Locataire</span>
									<span class="font-medium text-slate-900 dark:text-slate-100">
										{nomLocataire || '—'}
									</span>
								</div>
								<div class="flex justify-between">
									<span class="text-slate-500 dark:text-slate-400">Bien</span>
									<span
										class="max-w-[180px] truncate text-right font-medium text-slate-900 dark:text-slate-100"
									>
										{adresseBien || '—'}
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

							<!-- Date -->
							<div class="text-right text-xs text-slate-400 dark:text-slate-500">
								Payé le {datePaiement ? formatDateFr(datePaiement) : '—'}
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
								description="Entrez votre email pour débloquer le téléchargement. Un lien vous sera envoyé par email."
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

						<!-- CTA -->
						<div
							class="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-5 text-center dark:border-slate-700 dark:bg-slate-900"
						>
							<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">
								Pour générer vos quittances automatiquement chaque mois
							</p>
							<a href="/pricing">
								<Button size="lg" class="w-full bg-blue-600 text-white hover:bg-blue-700">
									Démarrer à 19€/mois
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

	<!-- Disclaimer -->
	<section class="pb-12">
		<div class="mx-auto max-w-6xl px-4 sm:px-6">
			<p class="text-center text-xs text-slate-400 dark:text-slate-500">
				Cette quittance est générée à titre indicatif conformément à l'article 21 de la loi
				n° 89-462 du 6 juillet 1989. Le bailleur est tenu de transmettre gratuitement la
				quittance au locataire qui en fait la demande. Ce document ne constitue pas un conseil
				juridique. Consultez un professionnel pour toute question.
			</p>
		</div>
	</section>
</main>
