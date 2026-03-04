<script lang="ts">
	import type { BienCreatePayload } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { buildBienPayload } from '$lib/high-value/biens';

	type BienFormSubmit = (payload: BienCreatePayload) => Promise<boolean | void> | boolean | void;

	export let title = 'Nouveau bien';
	export let description = 'Crée un bien pour alimenter le portefeuille SCI.';
	export let submitting = false;
	export let onSubmit: BienFormSubmit = () => true;

	let adresse = '';
	let ville = '';
	let loyerCC = '';
	let statut = 'occupe';

	async function handleSubmit() {
		const withRent = buildBienPayload({
			adresse,
			ville,
			loyerCC,
			statut
		});
		if (!withRent) {
			return;
		}

		const result = await onSubmit(withRent);
		if (result !== false) {
			adresse = '';
			ville = '';
			loyerCC = '';
			statut = 'occupe';
		}
	}
</script>

<Card class="sci-section-card">
	<CardHeader>
		<CardTitle class="text-lg">{title}</CardTitle>
		<CardDescription>{description}</CardDescription>
	</CardHeader>
	<CardContent>
		<form class="grid gap-3 md:grid-cols-4" on:submit|preventDefault={handleSubmit}>
			<label class="sci-field">
				<span class="sci-field-label">Adresse</span>
				<Input bind:value={adresse} required placeholder="14 rue Saint-Honoré" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Ville</span>
				<Input bind:value={ville} placeholder="Paris" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Loyer CC (€)</span>
				<Input bind:value={loyerCC} type="number" min="0" step="10" placeholder="1450" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Statut</span>
				<select bind:value={statut} class="sci-select">
					<option value="occupe">Occupé</option>
					<option value="vacant">Vacant</option>
					<option value="travaux">Travaux</option>
				</select>
			</label>
			<div class="md:col-span-4 flex justify-end">
				<Button type="submit" disabled={submitting} class="min-w-[11rem]">
					{submitting ? 'Ajout en cours...' : 'Ajouter le bien'}
				</Button>
			</div>
		</form>
	</CardContent>
</Card>
