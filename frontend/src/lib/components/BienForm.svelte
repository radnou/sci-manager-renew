<script lang="ts">
	import type { BienCreatePayload, BienType } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { buildBienPayload } from '$lib/high-value/biens';

	type BienFormSubmit = (payload: BienCreatePayload) => Promise<boolean | void> | boolean | void;

	let {
		title = 'Nouveau bien',
		description = 'Crée un bien pour alimenter le portefeuille SCI.',
		submitting = false,
		onSubmit = () => true
	}: {
		title?: string;
		description?: string;
		submitting?: boolean;
		onSubmit?: BienFormSubmit;
	} = $props();

	const defaultSciId = import.meta.env.VITE_DEFAULT_SCI_ID || 'sci-1';

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

	// Validation errors for accessibility
	let codePostalError = $state('');

	function validateCodePostal(value: string) {
		if (!value) return '';
		if (!/^\d{5}$/.test(value)) {
			return 'Le code postal doit contenir exactement 5 chiffres';
		}
		return '';
	}

	$effect(() => {
		codePostalError = validateCodePostal(codePostal);
	});

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		const payload = buildBienPayload({
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
		});
		if (!payload) {
			return;
		}

		const result = await onSubmit(payload);
		if (result !== false) {
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
	}
</script>

<Card class="sci-section-card">
	<CardHeader>
		<CardTitle class="text-lg">{title}</CardTitle>
		<CardDescription>{description}</CardDescription>
	</CardHeader>
	<CardContent>
		<form class="grid gap-3 md:grid-cols-4" onsubmit={handleSubmit} aria-label="Formulaire d'ajout de bien immobilier">
			<label for="bien-id-sci" class="sci-field">
				<span class="sci-field-label">ID SCI</span>
				<Input id="bien-id-sci" bind:value={idSci} required placeholder="sci-1" aria-required="true" />
			</label>
			<label for="bien-adresse" class="sci-field md:col-span-2">
				<span class="sci-field-label">Adresse</span>
				<Input id="bien-adresse" bind:value={adresse} required placeholder="14 rue Saint-Honoré" aria-required="true" />
			</label>
			<label for="bien-ville" class="sci-field">
				<span class="sci-field-label">Ville</span>
				<Input id="bien-ville" bind:value={ville} required placeholder="Paris" aria-required="true" />
			</label>
			<label for="bien-code-postal" class="sci-field">
				<span class="sci-field-label">Code postal</span>
				<Input
					id="bien-code-postal"
					bind:value={codePostal}
					required
					pattern="\\d{5}"
					placeholder="75001"
					aria-required="true"
					aria-describedby={codePostalError ? 'code-postal-error' : undefined}
					aria-invalid={!!codePostalError}
				/>
				{#if codePostalError}
					<span id="code-postal-error" role="alert" class="text-xs text-red-600 dark:text-red-400 mt-1">
						{codePostalError}
					</span>
				{/if}
			</label>
			<label for="bien-type-locatif" class="sci-field">
				<span class="sci-field-label">Type locatif</span>
				<select id="bien-type-locatif" bind:value={typeLocatif} class="sci-select" aria-label="Type de location">
					<option value="nu">Nu</option>
					<option value="meuble">Meublé</option>
					<option value="mixte">Mixte</option>
				</select>
			</label>
			<label for="bien-loyer-cc" class="sci-field">
				<span class="sci-field-label">Loyer CC (€)</span>
				<Input id="bien-loyer-cc" bind:value={loyerCC} type="number" min="0" step="10" placeholder="1450" />
			</label>
			<label for="bien-charges" class="sci-field">
				<span class="sci-field-label">Charges (€)</span>
				<Input id="bien-charges" bind:value={charges} type="number" min="0" step="10" placeholder="150" />
			</label>
			<label for="bien-tmi" class="sci-field">
				<span class="sci-field-label">TMI (%)</span>
				<Input id="bien-tmi" bind:value={tmi} type="number" min="0" max="100" step="0.5" placeholder="30" />
			</label>
			<label for="bien-acquisition-date" class="sci-field">
				<span class="sci-field-label">Date d'acquisition</span>
				<Input id="bien-acquisition-date" bind:value={acquisitionDate} type="date" aria-label="Date d'acquisition du bien" />
			</label>
			<label for="bien-prix-acquisition" class="sci-field">
				<span class="sci-field-label">Prix acquisition (€)</span>
				<Input id="bien-prix-acquisition" bind:value={prixAcquisition} type="number" min="0" step="1000" placeholder="250000" />
			</label>
			<div class="md:col-span-4 flex justify-end">
				<Button type="submit" disabled={submitting} class="min-w-[11rem]" aria-live="polite">
					{submitting ? 'Ajout en cours...' : 'Ajouter le bien'}
				</Button>
			</div>
		</form>
	</CardContent>
</Card>
