<script lang="ts">
	import type { Bien, BienCreatePayload, BienType, BienUpdatePayload } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { buildBienPayload, buildBienUpdatePayload } from '$lib/high-value/biens';

	type BienFormMode = 'create' | 'edit';
	type BienFormSubmit = (
		payload: BienCreatePayload | BienUpdatePayload
	) => Promise<boolean | void> | boolean | void;
	const defaultSciId = import.meta.env.VITE_DEFAULT_SCI_ID || 'sci-1';

	let {
		title = 'Nouveau bien',
		description = 'Crée un bien pour alimenter le portefeuille SCI.',
		mode = 'create',
		submitLabel = 'Ajouter le bien',
		cancelLabel = 'Annuler',
		activeSciId = defaultSciId,
		activeSciLabel = 'SCI active',
		showSciField = false,
		initialValues = null,
		submitting = false,
		onCancel = undefined,
		onSubmit = () => true
	}: {
		title?: string;
		description?: string;
		mode?: BienFormMode;
		submitLabel?: string;
		cancelLabel?: string;
		activeSciId?: string;
		activeSciLabel?: string;
		showSciField?: boolean;
		initialValues?: Bien | null;
		submitting?: boolean;
		onCancel?: (() => void) | undefined;
		onSubmit?: BienFormSubmit;
	} = $props();

	let idSci = $state(defaultSciId);
	let adresse = $state('');
	let ville = $state('');
	let codePostal = $state('');
	let typeLocatif = $state<BienType>('nu');
	let loyerCC = $state('');
	let charges = $state('');
	let tmi = $state('');
	let acquisitionDate = $state('');
	let prixAcquisition = $state('');
	let formElement: HTMLFormElement | null = null;

	// Validation errors for accessibility
	let codePostalError = $state('');
	let lastAppliedBienKey = $state('');

	function validateCodePostal(value: string) {
		if (!value) return '';
		if (!/^\d{5}$/.test(value)) {
			return 'Le code postal doit contenir exactement 5 chiffres';
		}
		return '';
	}

	function resetFormFields() {
		adresse = '';
		ville = '';
		codePostal = '';
		typeLocatif = 'nu';
		loyerCC = '';
		charges = '';
		tmi = '';
		acquisitionDate = '';
		prixAcquisition = '';
	}

	function applyBienValues(bien: Bien) {
		idSci = String(bien.id_sci || activeSciId || defaultSciId);
		adresse = bien.adresse || '';
		ville = bien.ville || '';
		codePostal = bien.code_postal || '';
		typeLocatif = (bien.type_locatif as BienType) || 'nu';
		loyerCC = bien.loyer_cc != null ? String(bien.loyer_cc) : '';
		charges = bien.charges != null ? String(bien.charges) : '';
		tmi = bien.tmi != null ? String(bien.tmi) : '';
		acquisitionDate = bien.acquisition_date || '';
		prixAcquisition = bien.prix_acquisition != null ? String(bien.prix_acquisition) : '';
	}

	$effect(() => {
		idSci = activeSciId || defaultSciId;
	});

	$effect(() => {
		if (mode !== 'edit' || !initialValues) {
			lastAppliedBienKey = '';
			return;
		}

		const nextKey = String(
			initialValues.id || `${initialValues.adresse}-${initialValues.code_postal || ''}`
		);
		if (lastAppliedBienKey === nextKey) {
			return;
		}

		applyBienValues(initialValues);
		lastAppliedBienKey = nextKey;
	});

	$effect(() => {
		codePostalError = validateCodePostal(codePostal);
	});

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		const formInput = {
			idSci,
			adresse,
			ville,
			codePostal,
			typeLocatif,
			loyerCC,
			charges,
			tmi,
			acquisitionDate,
			prixAcquisition
		};
		const payload =
			mode === 'edit' ? buildBienUpdatePayload(formInput) : buildBienPayload(formInput);
		if (!payload) {
			return;
		}

		const result = await onSubmit(payload);
		if (result !== false && mode === 'create') {
			resetFormFields();
		}
	}
</script>

<Card class="sci-section-card">
	<CardHeader>
		<CardTitle class="text-lg">{title}</CardTitle>
		<CardDescription>{description}</CardDescription>
	</CardHeader>
	<CardContent>
		<form
			bind:this={formElement}
			class="grid gap-3 md:grid-cols-4"
			onsubmit={handleSubmit}
			aria-label="Formulaire d'ajout de bien immobilier"
		>
			{#if showSciField}
				<label for="bien-id-sci" class="sci-field">
					<span class="sci-field-label">SCI</span>
					<Input
						id="bien-id-sci"
						bind:value={idSci}
						required
						placeholder="SCI principale"
						aria-required="true"
					/>
				</label>
			{:else}
				<div class="sci-field">
					<span class="sci-field-label">SCI rattachée</span>
					<div
						class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					>
						{activeSciLabel}
					</div>
				</div>
			{/if}
			<label for="bien-adresse" class="sci-field md:col-span-2">
				<span class="sci-field-label">Adresse</span>
				<Input
					id="bien-adresse"
					bind:value={adresse}
					required
					placeholder="14 rue Saint-Honoré"
					aria-required="true"
				/>
			</label>
			<label for="bien-ville" class="sci-field">
				<span class="sci-field-label">Ville</span>
				<Input
					id="bien-ville"
					bind:value={ville}
					required
					placeholder="Paris"
					aria-required="true"
				/>
			</label>
			<label for="bien-code-postal" class="sci-field">
				<span class="sci-field-label">Code postal</span>
				<Input
					id="bien-code-postal"
					bind:value={codePostal}
					required
					pattern="[0-9]{5}"
					placeholder="75001"
					aria-required="true"
					aria-describedby={codePostalError ? 'code-postal-error' : undefined}
					aria-invalid={!!codePostalError}
				/>
				{#if codePostalError}
					<span
						id="code-postal-error"
						role="alert"
						class="mt-1 text-xs text-red-600 dark:text-red-400"
					>
						{codePostalError}
					</span>
				{/if}
			</label>
			<label for="bien-type-locatif" class="sci-field">
				<span class="sci-field-label">Type locatif</span>
				<select
					id="bien-type-locatif"
					bind:value={typeLocatif}
					class="sci-select"
					aria-label="Type de location"
				>
					<option value="nu">Nu</option>
					<option value="meuble">Meublé</option>
					<option value="mixte">Mixte</option>
				</select>
			</label>
			<label for="bien-loyer-cc" class="sci-field">
				<span class="sci-field-label">Loyer CC (€)</span>
				<Input
					id="bien-loyer-cc"
					bind:value={loyerCC}
					type="number"
					min="0"
					step="10"
					placeholder="1450"
				/>
			</label>
			<label for="bien-charges" class="sci-field">
				<span class="sci-field-label">Charges (€)</span>
				<Input
					id="bien-charges"
					bind:value={charges}
					type="number"
					min="0"
					step="10"
					placeholder="150"
				/>
			</label>
			<label for="bien-tmi" class="sci-field">
				<span class="sci-field-label">TMI (%)</span>
				<Input
					id="bien-tmi"
					bind:value={tmi}
					type="number"
					min="0"
					max="100"
					step="0.5"
					placeholder="30"
				/>
			</label>
			<label for="bien-acquisition-date" class="sci-field">
				<span class="sci-field-label">Date d'acquisition</span>
				<Input
					id="bien-acquisition-date"
					bind:value={acquisitionDate}
					type="date"
					aria-label="Date d'acquisition du bien"
				/>
			</label>
			<label for="bien-prix-acquisition" class="sci-field">
				<span class="sci-field-label">Prix acquisition (€)</span>
				<Input
					id="bien-prix-acquisition"
					bind:value={prixAcquisition}
					type="number"
					min="0"
					step="1000"
					placeholder="250000"
				/>
			</label>
			<div class="flex justify-end gap-2 md:col-span-4">
				{#if mode === 'edit' && onCancel}
					<Button type="button" variant="outline" onclick={onCancel}>
						{cancelLabel}
					</Button>
				{/if}
				<Button
					type="button"
					disabled={submitting}
					class="min-w-[11rem]"
					aria-live="polite"
					onclick={() => {
						formElement?.requestSubmit();
					}}
				>
					{submitting ? (mode === 'edit' ? 'Enregistrement...' : 'Ajout en cours...') : submitLabel}
				</Button>
			</div>
		</form>
	</CardContent>
</Card>
