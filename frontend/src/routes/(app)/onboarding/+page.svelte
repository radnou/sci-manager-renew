<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Building2, Home, FileText, Bell, Sparkles } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import {
		createSci,
		createBien,
		completeOnboarding,
		fetchOnboardingStatus,
		type SCICreatePayload,
		type BienCreatePayload,
		type OnboardingStatus
	} from '$lib/api';

	let currentStep = $state(1);
	let status = $state<OnboardingStatus | null>(null);
	let loading = $state(true);
	let submitting = $state(false);
	let error = $state('');

	// Step 1: SCI
	let sciNom = $state('');
	let sciSiren = $state('');
	let sciRegime = $state<'IR' | 'IS'>('IR');
	let createdSciId = $state('');

	// Step 2: Bien
	let bienAdresse = $state('');
	let bienVille = $state('');
	let bienCodePostal = $state('');
	let bienType = $state<'nu' | 'meuble' | 'mixte'>('nu');
	let bienLoyerCc = $state(0);
	let bienCharges = $state(0);

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
			// Resume at the right step
			if (status.sci_created) currentStep = 2;
			if (status.bien_created) currentStep = 3;
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
			error = err instanceof Error ? err.message : 'Erreur lors de la création de la SCI.';
		} finally {
			submitting = false;
		}
	}

	async function handleStep2() {
		if (!bienAdresse.trim() || !bienVille.trim() || !bienCodePostal.trim()) {
			error = "L'adresse, la ville et le code postal sont requis.";
			return;
		}
		submitting = true;
		error = '';
		try {
			await createBien({
				id_sci: createdSciId,
				adresse: bienAdresse.trim(),
				ville: bienVille.trim(),
				code_postal: bienCodePostal.trim(),
				type_locatif: bienType,
				loyer_cc: bienLoyerCc,
				charges: bienCharges,
				tmi: 0
			} as BienCreatePayload);
			currentStep = 3;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Erreur lors de la création du bien.';
		} finally {
			submitting = false;
		}
	}

	function handleStep3() {
		// Bail configuration is optional during onboarding — skip for now
		currentStep = 4;
	}

	function handleStep4() {
		// Save notification preference (simplified — full config in settings later)
		currentStep = 5;
	}

	async function handleStep5() {
		submitting = true;
		error = '';
		try {
			await completeOnboarding();
			goto('/dashboard');
		} catch (err) {
			error =
				err instanceof Error ? err.message : "Erreur lors de la finalisation de l'onboarding.";
		} finally {
			submitting = false;
		}
	}
</script>

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
							placeholder="123 456 789"
							class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
						/>
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
				<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-slate-100">
					Ajoutez votre premier bien
				</h2>
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
							<label for="bien-loyer" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
								Loyer CC (€/mois)
							</label>
							<input
								id="bien-loyer"
								type="number"
								bind:value={bienLoyerCc}
								min="0"
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
								class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
							/>
						</div>
					</div>
				</div>
				<div class="mt-6 flex justify-end">
					<Button onclick={handleStep2} disabled={submitting}>
						{submitting ? 'Ajout...' : 'Ajouter le bien'}
					</Button>
				</div>

			{:else if currentStep === 3}
				<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-slate-100">
					Configuration du bail
				</h2>
				<p class="text-sm text-slate-600 dark:text-slate-400">
					Vous pourrez configurer le bail et ajouter un locataire depuis la fiche bien.
					Pour le moment, passons à l'étape suivante.
				</p>
				<div class="mt-6 flex justify-end">
					<Button onclick={handleStep3}>Continuer</Button>
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
					<Button onclick={handleStep4}>Continuer</Button>
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
