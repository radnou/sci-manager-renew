<script lang="ts">
	import { onMount } from 'svelte';
	import { goto, invalidateAll } from '$app/navigation';
	import { Building2, Home, FileText, Sparkles, UserCircle2 } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import Celebration from '$lib/components/Celebration.svelte';
	import { trackEvent } from '$lib/analytics';
	import {
		createSci,
		createBienForSci,
		createBail,
		createLocataire,
		attachLocataireToBail,
		completeOnboarding,
		fetchOnboardingStatus,
		fetchSciBiensList,
		saveOnboardingProfile,
		type SCICreatePayload,
		type BienCreatePayload,
		type BailCreate,
		type LocataireCreatePayload,
		type OnboardingStatus,
		type OnboardingProfile
	} from '$lib/api';

	let currentStep = $state(1);
	let status = $state<OnboardingStatus | null>(null);
	let loading = $state(true);
	let submitting = $state(false);
	let error = $state('');
	let batchProgress = $state(0);
	let batchTotal = $state(0);
	let showFinishCelebration = $state(false);
	let savedProfile = $state<OnboardingProfile | null>(null);

	// Step 1: Profile questions
	let profileRole = $state('');
	let profileVolume = $state('');
	let profileTool = $state('');
	let profilePriorities = $state<string[]>([]);

	// Step 2: SCI
	let sciNom = $state('');
	let sciSiren = $state('');
	let sciRegime = $state<'IR' | 'IS'>('IR');
	let createdSciId = $state('');
	// Optional legal fields
	let sciLegalOpen = $state(false);
	let sciCapitalSocial = $state('');
	let sciRcsVille = $state('');
	let sciRcsNumero = $state('');
	let sciNomGerant = $state('');
	let sciFormeJuridique = $state('');

	// Step 2: Bien (sub-steps: type → adresse → details+financier)
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

	// Step 3: Bail + Locataire
	let createdBienId = $state('');
	let bailDateDebut = $state(new Date().toISOString().slice(0, 10));
	let bailLoyerHc = $state(0);
	let bailChargesLocatives = $state(0);
	let locataireNom = $state('');
	let locataireEmail = $state('');

	const steps = [
		{ num: 1, label: 'Votre profil', icon: UserCircle2 },
		{ num: 2, label: 'Votre SCI', icon: Building2 },
		{ num: 3, label: 'Votre 1er bien', icon: Home },
		{ num: 4, label: 'Configuration bail', icon: FileText },
		{ num: 5, label: 'Bienvenue', icon: Sparkles }
	];

	onMount(async () => {
		try {
			status = await fetchOnboardingStatus();
			if (status.completed && status.sci_created) {
				goto('/dashboard');
				return;
			}
			// Resume at the right step based on progress
			if (status.profile_set) {
				currentStep = 2;
				if (status.profile) savedProfile = status.profile;
			}
			if (status.sci_created) {
				currentStep = 3;
				if (status.sci_id) createdSciId = String(status.sci_id);
			}
			if (status.bien_created) {
				currentStep = 4;
				// Resolve first bien ID for bail creation
				if (createdSciId) {
					try {
						const biens = await fetchSciBiensList(createdSciId);
						if (biens.length > 0) createdBienId = String(biens[0].id);
					} catch { /* continue without bienId */ }
				}
			}
			if (status.bail_created || status.notifications_set) currentStep = 5;
		} catch {
			// Continue with step 1
		} finally {
			loading = false;
		}
	});

	function togglePriority(value: string) {
		if (profilePriorities.includes(value)) {
			profilePriorities = profilePriorities.filter(p => p !== value);
		} else if (profilePriorities.length < 3) {
			profilePriorities = [...profilePriorities, value];
		}
	}

	async function handleProfileSubmit() {
		if (!profileRole) {
			error = 'Veuillez sélectionner votre profil.';
			return;
		}
		if (!profileVolume) {
			error = 'Veuillez indiquer le nombre de biens.';
			return;
		}
		if (!profileTool) {
			error = 'Veuillez indiquer votre outil actuel.';
			return;
		}
		if (profilePriorities.length === 0) {
			error = 'Veuillez sélectionner au moins une priorité.';
			return;
		}
		submitting = true;
		error = '';
		try {
			const profile = await saveOnboardingProfile({
				role: profileRole,
				volume: profileVolume,
				current_tool: profileTool,
				priorities: profilePriorities
			});
			savedProfile = profile;
			trackEvent('onboarding_profile_completed', {
				role: profileRole,
				volume: profileVolume,
				tool: profileTool,
				priorities: profilePriorities.join(',')
			});
			currentStep = 2;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Erreur lors de la sauvegarde du profil.';
		} finally {
			submitting = false;
		}
	}

	async function handleStep2() {
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
				regime_fiscal: sciRegime,
			capital_social: sciCapitalSocial ? parseFloat(sciCapitalSocial) : undefined,
			rcs_ville: sciRcsVille.trim() || undefined,
			rcs_numero: sciRcsNumero.trim() || undefined,
			nom_gerant: sciNomGerant.trim() || undefined,
			forme_juridique: sciFormeJuridique || undefined
			} as SCICreatePayload);
			createdSciId = String(sci.id);
			currentStep = 3;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Erreur lors de la création de la SCI.';
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
		}
	}

	function handleBienSubBack() {
		error = '';
		if (bienSubStep > 1) bienSubStep -= 1;
	}

	async function handleStep3Submit() {
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
				const lotSuffix = lotsToCreate > 1 ? ` — Lot ${i + 1}` : '';
				return {
					id_sci: createdSciId,
					adresse: bienAdresse.trim() + lotSuffix,
					ville: bienVille.trim(),
					code_postal: bienCodePostal.trim(),
					type_locatif: bienType,
					type_bien: bienCategorie,
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
				const results = await Promise.all(batch.map(p => createBienForSci(createdSciId, p)));
				for (const result of results) {
					if (result?.id) lastBienId = String(result.id);
				}
				batchProgress = Math.min(i + batch.length, lotsToCreate);
			}

			if (lastBienId) createdBienId = lastBienId;
			bailLoyerHc = bienLoyerCc > bienCharges ? bienLoyerCc - bienCharges : bienLoyerCc;
			bailChargesLocatives = bienCharges;
			batchTotal = 0;
			currentStep = 4;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Erreur lors de la création du bien.';
		} finally {
			submitting = false;
		}
	}

	async function handleStep4() {
		if (!createdBienId || !createdSciId) {
			// No bien created yet — skip bail creation gracefully
			currentStep = 5;
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
			const bail = await createBail(createdSciId, createdBienId, bailData);

			// Create and attach locataire if name is provided
			if (locataireNom.trim()) {
				try {
					const locataire = await createLocataire({
						id_bien: createdBienId,
						nom: locataireNom.trim(),
						email: locataireEmail.trim() || undefined,
						date_debut: bailDateDebut
					} as LocataireCreatePayload);
					if (locataire?.id && bail?.id) {
						await attachLocataireToBail(
							createdSciId,
							createdBienId,
							String(bail.id),
							String(locataire.id)
						);
					}
				} catch {
					// Non-blocking: bail is created, locataire attachment is best-effort
				}
			}

			currentStep = 5;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Erreur lors de la création du bail.';
		} finally {
			submitting = false;
		}
	}

	function handleSkipStep4() {
		currentStep = 5;
	}

	const ROLE_LABELS: Record<string, string> = {
		gerant_familial: 'gérant de SCI familiale',
		investisseur: 'investisseur patrimonial',
		professionnel: 'professionnel de la gestion',
		associe: 'associé'
	};

	const PRIORITY_ACTIONS: Record<string, { text: string; cta: string; destination: 'loyer' | 'dashboard' }> = {
		loyers: { text: 'Enregistrer votre premier loyer (2 clics)', cta: 'Enregistrer mon premier loyer', destination: 'loyer' },
		quittances: { text: 'Générer votre première quittance PDF', cta: 'Générer une quittance', destination: 'loyer' },
		fiscalite: { text: 'Préparer votre déclaration CERFA 2044', cta: 'Voir la fiscalité', destination: 'dashboard' },
		finances: { text: 'Consulter votre tableau de bord financier', cta: 'Voir le tableau de bord', destination: 'dashboard' },
		ag_parts: { text: 'Planifier votre première assemblée générale', cta: 'Voir le tableau de bord', destination: 'dashboard' }
	};

	const personalizedRoleLabel = $derived(
		savedProfile?.role ? (ROLE_LABELS[savedProfile.role] ?? '') : ''
	);

	const personalizedActions = $derived(
		(!savedProfile?.priorities?.length)
			? [
				{ text: 'Enregistrer votre premier loyer (2 clics)', destination: 'loyer' as const },
				{ text: 'Générer votre première quittance PDF', destination: 'loyer' as const },
				{ text: 'Configurer les alertes de retard', destination: 'dashboard' as const }
			]
			: savedProfile.priorities
				.map(p => PRIORITY_ACTIONS[p])
				.filter(Boolean)
				.map(a => ({ text: a.text, destination: a.destination }))
	);

	const personalizedCta = $derived((() => {
		if (!savedProfile?.priorities?.length) return { label: 'Enregistrer mon premier loyer →', destination: 'loyer' as const };
		const first = savedProfile.priorities[0];
		const action = PRIORITY_ACTIONS[first];
		return action ? { label: action.cta + ' →', destination: action.destination } : { label: 'Enregistrer mon premier loyer →', destination: 'loyer' as const };
	})());

	async function handleFinish(destination: 'loyer' | 'dashboard') {
		// Show celebration briefly before navigating
		showFinishCelebration = true;
		await new Promise((resolve) => setTimeout(resolve, 1500));

		submitting = true;
		error = '';
		try {
			await completeOnboarding();
			await invalidateAll();
			if (destination === 'loyer' && createdSciId && createdBienId) {
				await goto(`/scis/${createdSciId}/biens/${createdBienId}?tab=loyers`, { replaceState: true });
			} else {
				await goto('/dashboard', { replaceState: true });
			}
		} catch (err) {
			error =
				err instanceof Error ? err.message : "Erreur lors de la finalisation de l'onboarding.";
			submitting = false;
		}
	}
</script>

<svelte:head><title>Onboarding | GérerSCI</title></svelte:head>

<section class="mx-auto max-w-2xl px-4 py-12">
	<div class="mb-8 text-center">
		<h1 class="text-2xl font-bold text-slate-900 dark:text-slate-100">
			Bienvenue sur GérerSCI
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
					{#if step.num < steps.length}
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
					Parlons de vous
				</h2>
				<p class="mb-6 text-sm text-slate-600 dark:text-slate-400">
					Ces informations nous permettent de personnaliser votre expérience.
				</p>

				<!-- Q1: Role -->
				<div class="mb-6">
					<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">Quel est votre profil ?</p>
					<div class="grid grid-cols-2 gap-3">
						{#each [
							{ value: 'gerant_familial', label: 'Gérant de SCI familiale', emoji: '👨‍👩‍👧' },
							{ value: 'investisseur', label: 'Investisseur patrimonial', emoji: '📈' },
							{ value: 'professionnel', label: 'Expert-comptable / Gestionnaire', emoji: '💼' },
							{ value: 'associe', label: 'Associé (non gérant)', emoji: '👤' }
						] as option}
							<button
								type="button"
								onclick={() => { profileRole = option.value; }}
								class="flex items-center gap-3 rounded-xl border-2 p-3 text-left text-sm transition-all
									{profileRole === option.value
										? 'border-slate-900 bg-slate-50 dark:border-slate-100 dark:bg-slate-900'
										: 'border-slate-200 hover:border-slate-400 dark:border-slate-700 dark:hover:border-slate-500'}"
							>
								<span class="text-xl">{option.emoji}</span>
								<span class="font-medium text-slate-700 dark:text-slate-300">{option.label}</span>
							</button>
						{/each}
					</div>
				</div>

				<!-- Q2: Volume -->
				<div class="mb-6">
					<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">Combien de biens gérez-vous ?</p>
					<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
						{#each [
							{ value: '1-2', label: '1–2 biens' },
							{ value: '3-5', label: '3–5 biens' },
							{ value: '6-20', label: '6–20 biens' },
							{ value: '20+', label: '20+ biens' }
						] as option}
							<button
								type="button"
								onclick={() => { profileVolume = option.value; }}
								class="rounded-xl border-2 px-4 py-3 text-sm font-medium transition-all
									{profileVolume === option.value
										? 'border-slate-900 bg-slate-50 text-slate-900 dark:border-slate-100 dark:bg-slate-900 dark:text-slate-100'
										: 'border-slate-200 text-slate-600 hover:border-slate-400 dark:border-slate-700 dark:text-slate-400 dark:hover:border-slate-500'}"
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- Q3: Current tool -->
				<div class="mb-6">
					<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">Comment gérez-vous votre SCI aujourd'hui ?</p>
					<div class="grid grid-cols-2 gap-3">
						{#each [
							{ value: 'tableur', label: 'Tableur (Excel, Sheets…)', emoji: '📊' },
							{ value: 'comptable', label: 'Mon comptable s\'en charge', emoji: '🧮' },
							{ value: 'rien', label: 'Pas d\'outil structuré', emoji: '📝' },
							{ value: 'autre_logiciel', label: 'Un autre logiciel', emoji: '💻' }
						] as option}
							<button
								type="button"
								onclick={() => { profileTool = option.value; }}
								class="flex items-center gap-3 rounded-xl border-2 p-3 text-left text-sm transition-all
									{profileTool === option.value
										? 'border-slate-900 bg-slate-50 dark:border-slate-100 dark:bg-slate-900'
										: 'border-slate-200 hover:border-slate-400 dark:border-slate-700 dark:hover:border-slate-500'}"
							>
								<span class="text-xl">{option.emoji}</span>
								<span class="font-medium text-slate-700 dark:text-slate-300">{option.label}</span>
							</button>
						{/each}
					</div>
				</div>

				<!-- Q4: Priorities (multi-select) -->
				<div class="mb-6">
					<p class="mb-2 text-sm font-medium text-slate-700 dark:text-slate-300">Quelles sont vos priorités ?</p>
					<p class="mb-3 text-xs text-slate-500 dark:text-slate-400">Sélectionnez jusqu'à 3 réponses</p>
					<div class="flex flex-wrap gap-2">
						{#each [
							{ value: 'loyers', label: 'Suivi des loyers et relances' },
							{ value: 'quittances', label: 'Génération de quittances' },
							{ value: 'fiscalite', label: 'Déclarations fiscales (CERFA)' },
							{ value: 'finances', label: 'Vue financière consolidée' },
							{ value: 'ag_parts', label: 'Gestion des AG et parts' }
						] as option}
							<button
								type="button"
								onclick={() => togglePriority(option.value)}
								class="rounded-full border-2 px-4 py-2 text-sm transition-all
									{profilePriorities.includes(option.value)
										? 'border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-900'
										: profilePriorities.length >= 3
											? 'cursor-not-allowed border-slate-200 text-slate-400 dark:border-slate-700 dark:text-slate-600'
											: 'border-slate-200 text-slate-600 hover:border-slate-400 dark:border-slate-700 dark:text-slate-400 dark:hover:border-slate-500'}"
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<div class="mt-6 flex justify-end">
					<Button onclick={handleProfileSubmit} disabled={submitting}>
						{submitting ? 'Enregistrement...' : 'Continuer'}
					</Button>
				</div>

			{:else if currentStep === 2}
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

				<!-- Optional legal fields (collapsible) -->
				<div class="mt-4 rounded-lg border border-slate-200 dark:border-slate-700">
					<button
						type="button"
						onclick={() => sciLegalOpen = !sciLegalOpen}
						class="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800"
					>
						<span>Informations légales (optionnel)</span>
						<svg class="h-4 w-4 transition-transform {sciLegalOpen ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
					</button>
					{#if sciLegalOpen}
						<div class="border-t border-slate-200 px-4 py-4 dark:border-slate-700">
							<div class="space-y-3">
								<div class="grid grid-cols-2 gap-3">
									<div>
										<label for="sci-capital" class="mb-1 block text-sm text-slate-600 dark:text-slate-400">
											Capital social (EUR)
										</label>
										<input
											id="sci-capital"
											type="number"
											bind:value={sciCapitalSocial}
											min="0"
											placeholder="150 000"
											class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
										/>
									</div>
									<div>
										<label for="sci-rcs-ville" class="mb-1 block text-sm text-slate-600 dark:text-slate-400">
											RCS Ville
										</label>
										<input
											id="sci-rcs-ville"
											type="text"
											bind:value={sciRcsVille}
											placeholder="Paris"
											class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
										/>
									</div>
								</div>
								<div class="grid grid-cols-2 gap-3">
									<div>
										<label for="sci-rcs-numero" class="mb-1 block text-sm text-slate-600 dark:text-slate-400">
											RCS Numéro
										</label>
										<input
											id="sci-rcs-numero"
											type="text"
											bind:value={sciRcsNumero}
											placeholder="123 456 789"
											class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
										/>
									</div>
									<div>
										<label for="sci-nom-gerant" class="mb-1 block text-sm text-slate-600 dark:text-slate-400">
											Nom du gérant
										</label>
										<input
											id="sci-nom-gerant"
											type="text"
											bind:value={sciNomGerant}
											placeholder="Marie Dupont"
											class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
										/>
									</div>
								</div>
								<div>
									<label for="sci-forme-juridique" class="mb-1 block text-sm text-slate-600 dark:text-slate-400">
										Forme juridique
									</label>
									<select
										id="sci-forme-juridique"
										bind:value={sciFormeJuridique}
										class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
									>
										<option value="">Non renseignée</option>
										<option value="SCI">SCI</option>
										<option value="SARL">SARL</option>
										<option value="SAS">SAS</option>
										<option value="Autre">Autre</option>
									</select>
								</div>
							</div>
						</div>
					{/if}
				</div>

				<div class="mt-6 flex justify-end">
					<Button onclick={handleStep2} disabled={submitting}>
						{submitting ? 'Création...' : 'Créer la SCI'}
					</Button>
				</div>

			{:else if currentStep === 3}
				<div class="mb-4">
					<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
						Ajoutez votre premier bien
					</h2>
					<!-- Sub-step progress (3 sub-steps now) -->
					<div class="mt-3 flex items-center gap-2">
						{#each [1, 2, 3] as ss}
							<div class="h-1.5 flex-1 rounded-full transition-colors {bienSubStep >= ss ? 'bg-slate-900 dark:bg-slate-100' : 'bg-slate-200 dark:bg-slate-800'}"></div>
						{/each}
					</div>
					<p class="mt-2 text-xs text-slate-500">
						{bienSubStep === 1 ? 'Type de bien' : bienSubStep === 2 ? 'Adresse' : 'Caractéristiques et loyer'}
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
					<!-- Sub-step 3: Details + Financial (merged) -->
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
							<span id="onboarding-dpe-label" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
								DPE (Diagnostic de Performance Énergétique)
							</span>
							<div class="flex gap-2" role="group" aria-labelledby="onboarding-dpe-label">
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

						<!-- Financial fields -->
						<div class="mt-2 border-t border-slate-200 pt-4 dark:border-slate-700">
							<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">Loyer et charges</p>
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
								<div class="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950">
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
						{#if bienSubStep < 3}
							<Button onclick={handleBienSubNext}>Suivant</Button>
						{:else}
							<Button onclick={handleStep3Submit} disabled={submitting}>
								{submitting && batchTotal > 1 ? `Création ${batchProgress}/${batchTotal}...` : submitting ? 'Création...' : bienCategorie === 'immeuble' && bienNbLots > 1 ? `Créer ${bienNbLots} lots` : 'Ajouter le bien'}
							</Button>
						{/if}
					</div>
				</div>

			{:else if currentStep === 4}
				<h2 class="mb-6 text-lg font-semibold text-slate-900 dark:text-slate-100">
					Configuration du bail
				</h2>
				<p class="mb-4 text-sm text-slate-600 dark:text-slate-400">
					Créez un premier bail et renseignez votre locataire.
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
							{#if bailLoyerHc <= 0}
								<p class="mt-1 text-xs text-amber-600 dark:text-amber-400">Saisissez un loyer supérieur à 0€</p>
							{/if}
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

					<!-- Locataire section -->
					<div class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
						<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">Locataire (optionnel)</p>
						<div class="space-y-3">
							<div>
								<label for="locataire-nom" class="mb-1 block text-sm text-slate-600 dark:text-slate-400">
									Nom du locataire
								</label>
								<input
									id="locataire-nom"
									type="text"
									bind:value={locataireNom}
									placeholder="Jean Dupont"
									class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800"
								/>
							</div>
							<div>
								<label for="locataire-email" class="mb-1 block text-sm text-slate-600 dark:text-slate-400">
									Email du locataire
								</label>
								<input
									id="locataire-email"
									type="email"
									bind:value={locataireEmail}
									placeholder="jean.dupont@email.com"
									class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800"
								/>
							</div>
						</div>
					</div>
				</div>
				<div class="mt-6 flex items-center justify-between">
					<button
						type="button"
						onclick={handleSkipStep4}
						class="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
					>
						Passer cette étape
					</button>
					<Button onclick={handleStep4} disabled={submitting || !bailDateDebut || bailLoyerHc <= 0}>
						{submitting ? 'Création...' : 'Créer le bail'}
					</Button>
				</div>

			{:else if currentStep === 5}
				<div class="text-center">
					<div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900">
						<Sparkles class="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
					</div>
					<h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
						Votre SCI « {sciNom} » est configurée !
					</h2>
					{#if personalizedRoleLabel}
						<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
							En tant que <strong>{personalizedRoleLabel}</strong>, voici ce que GérerSCI va faire pour vous :
						</p>
					{:else}
						<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
							Voici ce que GérerSCI a préparé pour vous :
						</p>
					{/if}

					<!-- KPI preview cards -->
					<div class="mt-6 grid grid-cols-3 gap-3">
						{#each [
							{ label: 'Bien actif', value: '1', icon: '🏠' },
							{ label: 'Bail en cours', value: '1', icon: '📄' },
							{ label: 'Prochain loyer', value: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }), icon: '📅' }
						] as kpi, i}
							<div
								class="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800"
								style="animation: fadeInUp 0.4s ease-out {i * 100}ms both"
							>
								<span class="text-2xl">{kpi.icon}</span>
								<p class="mt-2 text-lg font-bold text-slate-900 dark:text-slate-100">{kpi.value}</p>
								<p class="text-xs text-slate-500 dark:text-slate-400">{kpi.label}</p>
							</div>
						{/each}
					</div>

					<!-- Personalized next actions -->
					<div class="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-left dark:border-slate-700 dark:bg-slate-800">
						<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">
							{#if savedProfile?.priorities?.length}
								Vos priorités, nos suggestions :
							{:else}
								Prochaines actions suggérées :
							{/if}
						</p>
						<ul class="space-y-2 text-sm text-slate-600 dark:text-slate-400">
							{#each personalizedActions as action}
								<li class="flex items-center gap-2"><span class="text-emerald-500">→</span> {action.text}</li>
							{/each}
						</ul>
					</div>

					<div class="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
						<Button onclick={() => handleFinish(personalizedCta.destination)} disabled={submitting}>
							{submitting ? 'Finalisation...' : personalizedCta.label}
						</Button>
						<Button variant="outline" onclick={() => handleFinish('dashboard')} disabled={submitting}>
							Voir le tableau de bord
						</Button>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</section>

{#if showFinishCelebration}
	<Celebration
		type="confetti"
		title="C'est parti !"
		subtitle="Votre SCI est prête à être pilotée."
		duration={1500}
	/>
{/if}

<style>
	@keyframes fadeInUp {
		from { opacity: 0; transform: translateY(12px); }
		to { opacity: 1; transform: translateY(0); }
	}
</style>
