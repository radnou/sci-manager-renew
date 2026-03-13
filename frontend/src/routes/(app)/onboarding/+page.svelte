<script lang="ts">
	import { onMount } from 'svelte';
	import { goto, invalidateAll } from '$app/navigation';
	import { Building2, Home, FileText, Bell, Sparkles } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import {
		createSci,
		createBien,
		createBail,
		completeOnboarding,
		fetchOnboardingStatus,
		fetchSciBiensList,
		updateNotificationPreferences,
		type SCICreatePayload,
		type BienCreatePayload,
		type BailCreate,
		type OnboardingStatus
	} from '$lib/api';

	let currentStep = $state(1);
	let status = $state<OnboardingStatus | null>(null);
	let loading = $state(true);
	let submitting = $state(false);
	let error = $state('');
	let batchProgress = $state(0);
	let batchTotal = $state(0);

	// Step 1: SCI
	let sciNom = $state('');
	let sciSiren = $state('');
	let sciRegime = $state<'IR' | 'IS'>('IR');
	let createdSciId = $state('');

	// Step 2: Bien (sub-steps: type → adresse → details → financier)
	let bienSubStep = $state(1);
	let bienCategorie = $state<'appartement' | 'maison' | 'immeuble' | 'local_commercial' | 'parking' | 'autre'>('appartement');
	let bienAdresse = $state('');
	let bienVille = $state('');
	let bienCodePostal = $state('');
	let bienType = $state<'nu' | 'meuble' | 'mixte'>('nu');
	let bienSurface = $state<number | undefined>(undefined);
	let bienNbPieces = $state<number | undefined>(undefined);
	let bienDpe = $state<'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | ''>('');
	let bienLoyerCc = $state(0);
	let bienCharges = $state(0);
	let bienNbLots = $state(1);

	// Step 3: Bail
	let createdBienId = $state('');
	let bailDateDebut = $state(new Date().toISOString().slice(0, 10));
	let bailLoyerHc = $state(0);
	let bailChargesLocatives = $state(0);

	// Step 4: Notifications
	let emailAlertes = $state(true);

	const steps = [
		{ num: 1, label: 'Votre SCI', icon: Building2 },
		{ num: 2, label: 'Votre 1er bien', icon: Home },
		{ num: 3, label: 'Configuration bail', icon: FileText },
		{ num: 4, label: 'Notifications', icon: Bell },
		{ num: 5, label: 'Bienvenue', icon: Sparkles }
	];

	onMount(async () => {
		try {
			status = await fetchOnboardingStatus();
			if (status.completed) {
				goto('/dashboard');
				return;
			}
			// Resume at the right step, restoring createdSciId from status
			if (status.sci_created) {
				currentStep = 2;
				if (status.sci_id) createdSciId = String(status.sci_id);
			}
			if (status.bien_created) {
				currentStep = 3;
				// Resolve first bien ID for bail creation
				if (createdSciId) {
					try {
						const biens = await fetchSciBiensList(createdSciId);
						if (biens.length > 0) createdBienId = String(biens[0].id);
					} catch { /* continue without bienId */ }
				}
			}
			if (status.bail_created) currentStep = 4;
			if (status.notifications_set) currentStep = 5;
		} catch {
			// Continue with step 1
		} finally {
			loading = false;
		}
	});

	async function handleStep1() {
		if (!sciNom.trim()) {
			error = 'Le nom de la SCI est requis.';
			return;
		}
		submitting = true;
		error = '';
		try {
			const sci = await createSci({
				nom: sciNom.trim(),
				siren: sciSiren.trim() || undefined,
				regime_fiscal: sciRegime
			} as SCICreatePayload);
			createdSciId = String(sci.id);
			currentStep = 2;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Erreur lors de la cr\u00e9ation de la SCI.';
		} finally {
			submitting = false;
		}
	}

	function handleBienSubNext() {
		error = '';
		if (bienSubStep === 1) {
			bienSubStep = 2;
		} else if (bienSubStep === 2) {
			if (!bienAdresse.trim() || !bienVille.trim() || !bienCodePostal.trim()) {
				error = "L'adresse, la ville et le code postal sont requis.";
				return;
			}
			bienSubStep = 3;
		} else if (bienSubStep === 3) {
			bienSubStep = 4;
		}
	}

	function handleBienSubBack() {
		error = '';
		if (bienSubStep > 1) bienSubStep -= 1;
	}

	async function handleStep2Submit() {
		if (!bienAdresse.trim() || !bienVille.trim() || !bienCodePostal.trim()) {
			error = "L'adresse, la ville et le code postal sont requis.";
			return;
		}
		submitting = true;
		error = '';
		try {
			const lotsToCreate = bienCategorie === 'immeuble' && bienNbLots > 1 ? bienNbLots : 1;
			batchTotal = lotsToCreate;
			batchProgress = 0;
			let lastBienId: string | null = null;

			// Build all payloads
			const payloads = Array.from({ length: lotsToCreate }, (_, i) => {
				const lotSuffix = lotsToCreate > 1 ? ` \u2014 Lot ${i + 1}` : '';
				return {
					id_sci: createdSciId,
					adresse: bienAdresse.trim() + lotSuffix,
					ville: bienVille.trim(),
					code_postal: bienCodePostal.trim(),
					type_locatif: bienType,
					loyer_cc: bienLoyerCc,
					charges: bienCharges,
					tmi: 0,
					surface_m2: bienSurface || undefined,
					nb_pieces: bienNbPieces || undefined,
					dpe_classe: bienDpe || undefined
				} as BienCreatePayload;
			});

			// Process in batches of 5
			const BATCH_SIZE = 5;
			for (let i = 0; i < payloads.length; i += BATCH_SIZE) {
				const batch = payloads.slice(i, i + BATCH_SIZE);
				const results = await Promise.all(batch.map(p => createBien(p)));
				for (const result of results) {
					if (result?.id) lastBienId = String(result.id);
				}
				batchProgress = Math.min(i + batch.length, lotsToCreate);
			}

			if (lastBienId) createdBienId = lastBienId;
			bailLoyerHc = bienLoyerCc > bienCharges ? bienLoyerCc - bienCharges : bienLoyerCc;
			bailChargesLocatives = bienCharges;
			batchTotal = 0;
			currentStep = 3;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Erreur lors de la cr\u00e9ation du bien.';
		} finally {
			submitting = false;
		}
	}

	async function handleStep3() {
		if (!createdBienId || !createdSciId) {
			// No bien created yet — skip bail creation gracefully
			currentStep = 4;
			return;
		}
		submitting = true;
		error = '';
		try {
			const bailData: BailCreate = {
				date_debut: bailDateDebut,
				loyer_hc: bailLoyerHc,
				charges_locatives: bailChargesLocatives || undefined
			};
			await createBail(createdSciId, createdBienId, bailData);
			currentStep = 4;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Erreur lors de la cr\u00e9ation du bail.';
		} finally {
			submitting = false;
		}
	}

	function handleSkipStep3() {
		currentStep = 4;
	}

	async function handleStep4() {
		submitting = true;
		error = '';
		try {
			const DEFAULT_TYPES = [
				'late_payment', 'bail_expiring', 'quittance_pending',
				'pno_expiring', 'new_loyer', 'new_associe', 'subscription_expiring'
			];
			const preferences = DEFAULT_TYPES.map((type) => ({
				type,
				email_enabled: emailAlertes,
				in_app_enabled: true
			}));
			await updateNotificationPreferences(preferences);
			currentStep = 5;
		} catch {
			// Non-blocking — continue even if preferences fail
			currentStep = 5;
		} finally {
			submitting = false;
		}
	}

	async function handleStep5() {
		submitting = true;
		error = '';
		try {
			await completeOnboarding();
			await invalidateAll();
			await goto('/dashboard', { replaceState: true });
		} catch (err) {
			error =
				err instanceof Error ? err.message : "Erreur lors de la finalisation de l'onboarding.";
			submitting = false;
		}
	}
</script>

<svelte:head><title>Onboarding | GererSCI</title></svelte:head>

<section class="mx-auto max-w-2xl px-4 py-12">
	<div class="mb-8 text-center">
		<h1 class="text-2xl font-bold text-slate-900 dark:text-slate-100">
			Bienvenue sur GererSCI
		</h1>
		<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
			Configurons votre espace en quelques étapes.
		</p>
	</div>

	{#if loading}
		<div class="flex justify-center py-12">
			<div
				class="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900 dark:border-slate-700 dark:border-t-slate-100"
			></div>
		</div>
	{:else}
		<!-- Progress bar -->
		<div class="mb-8">
			<div class="flex items-center justify-between">
				{#each steps as step}
					<div class="flex flex-col items-center gap-1">
						<div
							class="flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold transition-colors
								{currentStep > step.num
								? 'bg-emerald-500 text-white'
								: currentStep === step.num
									? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
									: 'bg-slate-200 text-slate-500 dark:bg-slate-800 dark:text-slate-400'}"
						>
							{#if currentStep > step.num}
								&#10003;
							{:else}
								{step.num}
							{/if}
						</div>
						<span class="hidden text-xs text-slate-500 sm:block">{step.label}</span>
					</div>
					{#if step.num < 5}
						<div
							class="mx-1 h-0.5 flex-1 {currentStep > step.num
								? 'bg-emerald-500'
								: 'bg-slate-200 dark:bg-slate-800'}"
						></div>
					{/if}
				{/each}
			</div>
		</div>

		{#if error}
			<div class="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700 dark:bg-rose-950 dark:text-rose-300">
				{error}
			</div>
		{/if}

		<!-- Step content -->
		<div
			class="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-950"
		>
			{#if currentStep === 1}
				<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-slate-100">
					Créez votre première SCI
				</h2>
				<div class="space-y-4">
					<div>
						<label for="sci-nom" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
							Nom de la SCI *
						</label>
						<input
							id="sci-nom"
							type="text"
							bind:value={sciNom}
							placeholder="Ex: SCI Dupont Immobilier"
							class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
						/>
					</div>
					<div>
						<label for="sci-siren" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
							SIREN (optionnel)
						</label>
						<input
							id="sci-siren"
							type="text"
							bind:value={sciSiren}
							placeholder="123456789"
							pattern="\d{9}"
							maxlength={9}
							inputmode="numeric"
							class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
						/>
						{#if sciSiren && !/^\d{9}$/.test(sciSiren.replace(/\s/g, ''))}
							<p class="mt-1 text-xs text-rose-600 dark:text-rose-400">Le SIREN doit contenir exactement 9 chiffres</p>
						{/if}
					</div>
					<div>
						<label for="sci-regime" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
							Régime fiscal
						</label>
						<select
							id="sci-regime"
							bind:value={sciRegime}
							class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
						>
							<option value="IR">IR (Impôt sur le Revenu)</option>
							<option value="IS">IS (Impôt sur les Sociétés)</option>
						</select>
					</div>
				</div>
				<div class="mt-6 flex justify-end">
					<Button onclick={handleStep1} disabled={submitting}>
						{submitting ? 'Création...' : 'Créer la SCI'}
					</Button>
				</div>

			{:else if currentStep === 2}
				<div class="mb-4">
					<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
						Ajoutez votre premier bien
					</h2>
					<!-- Sub-step progress -->
					<div class="mt-3 flex items-center gap-2">
						{#each [1, 2, 3, 4] as ss}
							<div class="h-1.5 flex-1 rounded-full transition-colors {bienSubStep >= ss ? 'bg-slate-900 dark:bg-slate-100' : 'bg-slate-200 dark:bg-slate-800'}"></div>
						{/each}
					</div>
					<p class="mt-2 text-xs text-slate-500">
						{bienSubStep === 1 ? 'Type de bien' : bienSubStep === 2 ? 'Adresse' : bienSubStep === 3 ? 'Caractéristiques' : 'Loyer et charges'}
					</p>
				</div>

				{#if bienSubStep === 1}
					<!-- Sub-step 1: Category -->
					<p class="mb-4 text-sm text-slate-600 dark:text-slate-400">Quel type de bien souhaitez-vous ajouter ?</p>
					<div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
						{#each [
							{ value: 'appartement', label: 'Appartement', emoji: '🏢' },
							{ value: 'maison', label: 'Maison', emoji: '🏠' },
							{ value: 'immeuble', label: 'Immeuble', emoji: '🏗️' },
							{ value: 'local_commercial', label: 'Local commercial', emoji: '🏪' },
							{ value: 'parking', label: 'Parking / Box', emoji: '🅿️' },
							{ value: 'autre', label: 'Autre', emoji: '📦' }
						] as cat}
							<button
								type="button"
								onclick={() => { bienCategorie = cat.value as typeof bienCategorie; }}
								class="flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-sm transition-all
									{bienCategorie === cat.value
										? 'border-slate-900 bg-slate-50 dark:border-slate-100 dark:bg-slate-900'
										: 'border-slate-200 hover:border-slate-400 dark:border-slate-700 dark:hover:border-slate-500'}"
							>
								<span class="text-2xl">{cat.emoji}</span>
								<span class="font-medium text-slate-700 dark:text-slate-300">{cat.label}</span>
							</button>
						{/each}
					</div>

				{:else if bienSubStep === 2}
					<!-- Sub-step 2: Address -->
					<div class="space-y-4">
						<div>
							<label for="bien-adresse" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
								Adresse *
							</label>
							<input
								id="bien-adresse"
								type="text"
								bind:value={bienAdresse}
								placeholder="12 rue de la Paix"
								class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
							/>
						</div>
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label for="bien-ville" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Ville *
								</label>
								<input
									id="bien-ville"
									type="text"
									bind:value={bienVille}
									placeholder="Paris"
									class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
								/>
							</div>
							<div>
								<label for="bien-cp" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Code postal *
								</label>
								<input
									id="bien-cp"
									type="text"
									bind:value={bienCodePostal}
									placeholder="75002"
									class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
								/>
							</div>
						</div>
					</div>

				{:else if bienSubStep === 3}
					<!-- Sub-step 3: Details -->
					<div class="space-y-4">
						<div>
							<label for="bien-type" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
								Type de location
							</label>
							<select
								id="bien-type"
								bind:value={bienType}
								class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
							>
								<option value="nu">Location nue</option>
								<option value="meuble">Meublé</option>
								<option value="mixte">Mixte</option>
							</select>
						</div>
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label for="bien-surface" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Surface (m²)
								</label>
								<input
									id="bien-surface"
									type="number"
									bind:value={bienSurface}
									min="1"
									placeholder="45"
									class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
								/>
							</div>
							<div>
								<label for="bien-pieces" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Nombre de pièces
								</label>
								<input
									id="bien-pieces"
									type="number"
									bind:value={bienNbPieces}
									min="1"
									placeholder="3"
									class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
								/>
							</div>
						</div>
						<div>
							<label class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
								DPE (Diagnostic de Performance Énergétique)
							</label>
							<div class="flex gap-2">
								{#each ['A', 'B', 'C', 'D', 'E', 'F', 'G'] as classe}
									<button
										type="button"
										onclick={() => { bienDpe = bienDpe === classe ? '' : classe as typeof bienDpe; }}
										class="flex h-9 w-9 items-center justify-center rounded-lg text-xs font-bold transition-all
											{bienDpe === classe
												? classe <= 'B' ? 'bg-emerald-500 text-white' : classe <= 'D' ? 'bg-amber-500 text-white' : 'bg-rose-500 text-white'
												: 'border border-slate-300 text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800'}"
									>
										{classe}
									</button>
								{/each}
							</div>
						</div>
					</div>

				{:else if bienSubStep === 4}
					<!-- Sub-step 4: Financial + lots -->
					<div class="space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label for="bien-loyer" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Loyer CC (€/mois)
								</label>
								<input
									id="bien-loyer"
									type="number"
									bind:value={bienLoyerCc}
									min="0"
									placeholder="850"
									class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
								/>
							</div>
							<div>
								<label for="bien-charges" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
									Charges (€/mois)
								</label>
								<input
									id="bien-charges"
									type="number"
									bind:value={bienCharges}
									min="0"
									placeholder="50"
									class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
								/>
							</div>
						</div>

						{#if bienCategorie === 'immeuble'}
							<div class="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950">
								<label for="bien-lots" class="mb-1 block text-sm font-medium text-blue-800 dark:text-blue-300">
									Nombre de lots (appartements)
								</label>
								<p class="mb-2 text-xs text-blue-600 dark:text-blue-400">
									Chaque lot sera créé séparément avec le même loyer et les mêmes charges. Vous pourrez les modifier individuellement ensuite.
								</p>
								<input
									id="bien-lots"
									type="number"
									bind:value={bienNbLots}
									min="1"
									max="50"
									class="w-24 rounded-lg border border-blue-300 px-3 py-2 text-sm dark:border-blue-700 dark:bg-blue-900"
								/>
							</div>
						{/if}
					</div>
				{/if}

				<!-- Sub-step navigation -->
				<div class="mt-6 flex items-center justify-between">
					<div>
						{#if bienSubStep > 1}
							<Button variant="outline" onclick={handleBienSubBack}>Retour</Button>
						{/if}
					</div>
					<div>
						{#if bienSubStep < 4}
							<Button onclick={handleBienSubNext}>Suivant</Button>
						{:else}
							<Button onclick={handleStep2Submit} disabled={submitting}>
								{submitting && batchTotal > 1 ? `Création ${batchProgress}/${batchTotal}...` : submitting ? 'Création...' : bienCategorie === 'immeuble' && bienNbLots > 1 ? `Créer ${bienNbLots} lots` : 'Ajouter le bien'}
							</Button>
						{/if}
					</div>
				</div>

			{:else if currentStep === 3}
				<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-slate-100">
					Configuration du bail
				</h2>
				<p class="mb-4 text-sm text-slate-600 dark:text-slate-400">
					Créez un premier bail pour votre bien. Vous pourrez ajouter le locataire depuis la fiche bien.
				</p>
				<div class="space-y-4">
					<div>
						<label for="bail-date" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
							Date de début du bail *
						</label>
						<input
							id="bail-date"
							type="date"
							bind:value={bailDateDebut}
							class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
						/>
					</div>
					<div class="grid grid-cols-2 gap-4">
						<div>
							<label for="bail-loyer" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
								Loyer HC (€/mois) *
							</label>
							<input
								id="bail-loyer"
								type="number"
								bind:value={bailLoyerHc}
								min="0"
								placeholder="800"
								class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
							/>
						</div>
						<div>
							<label for="bail-charges" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
								Charges locatives (€/mois)
							</label>
							<input
								id="bail-charges"
								type="number"
								bind:value={bailChargesLocatives}
								min="0"
								placeholder="50"
								class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
							/>
						</div>
					</div>
				</div>
				<div class="mt-6 flex items-center justify-between">
					<button
						type="button"
						onclick={handleSkipStep3}
						class="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
					>
						Passer cette étape
					</button>
					<Button onclick={handleStep3} disabled={submitting || !bailDateDebut || bailLoyerHc <= 0}>
						{submitting ? 'Création...' : 'Créer le bail'}
					</Button>
				</div>

			{:else if currentStep === 4}
				<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-slate-100">
					Préférences de notifications
				</h2>
				<p class="mb-4 text-sm text-slate-600 dark:text-slate-400">
					Souhaitez-vous recevoir des alertes par email ?
				</p>
				<div class="flex items-center gap-3">
					<label class="flex cursor-pointer items-center gap-2">
						<input type="checkbox" bind:checked={emailAlertes} class="h-4 w-4 rounded" />
						<span class="text-sm text-slate-700 dark:text-slate-300">
							Recevoir les alertes par email (loyers en retard, baux expirant, etc.)
						</span>
					</label>
				</div>
				<div class="mt-6 flex justify-end">
					<Button onclick={handleStep4} disabled={submitting}>
						{submitting ? 'Enregistrement...' : 'Continuer'}
					</Button>
				</div>

			{:else if currentStep === 5}
				<div class="text-center">
					<div
						class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900"
					>
						<Sparkles class="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
					</div>
					<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
						Tout est prêt !
					</h2>
					<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
						Votre SCI est configurée. Accédez à votre tableau de bord pour commencer à gérer
						votre patrimoine.
					</p>
					<div class="mt-6">
						<Button onclick={handleStep5} disabled={submitting}>
							{submitting ? 'Finalisation...' : 'Accéder au dashboard'}
						</Button>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</section>
