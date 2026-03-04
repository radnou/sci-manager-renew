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
		<form class="grid gap-3 md:grid-cols-4" onsubmit={handleSubmit}>
			<label class="sci-field">
				<span class="sci-field-label">ID SCI</span>
				<Input bind:value={idSci} required placeholder="sci-1" />
			</label>
			<label class="sci-field md:col-span-2">
				<span class="sci-field-label">Adresse</span>
				<Input bind:value={adresse} required placeholder="14 rue Saint-Honoré" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Ville</span>
				<Input bind:value={ville} required placeholder="Paris" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Code postal</span>
				<Input bind:value={codePostal} required pattern="\\d{5}" placeholder="75001" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Type locatif</span>
				<select bind:value={typeLocatif} class="sci-select">
					<option value="nu">Nu</option>
					<option value="meuble">Meublé</option>
					<option value="mixte">Mixte</option>
				</select>
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Loyer CC (€)</span>
				<Input bind:value={loyerCC} type="number" min="0" step="10" placeholder="1450" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Charges (€)</span>
				<Input bind:value={charges} type="number" min="0" step="10" placeholder="150" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">TMI (%)</span>
				<Input bind:value={tmi} type="number" min="0" max="100" step="0.5" placeholder="30" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Acquisition</span>
				<Input bind:value={acquisitionDate} type="date" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Prix acquisition (€)</span>
				<Input bind:value={prixAcquisition} type="number" min="0" step="1000" placeholder="250000" />
			</label>
			<div class="md:col-span-4 flex justify-end">
				<Button type="submit" disabled={submitting} class="min-w-[11rem]">
					{submitting ? 'Ajout en cours...' : 'Ajouter le bien'}
				</Button>
			</div>
		</form>
	</CardContent>
</Card>
