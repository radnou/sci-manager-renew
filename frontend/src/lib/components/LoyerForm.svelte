<script lang="ts">
	import type { LoyerCreatePayload, LoyerStatus } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { buildLoyerPayload } from '$lib/high-value/loyers';

	type LoyerFormSubmit = (payload: LoyerCreatePayload) => Promise<boolean | void> | boolean | void;

	let {
		title = 'Nouveau loyer',
		description = 'Enregistre un paiement mensuel pour un bien.',
		submitting = false,
		onSubmit = () => true
	}: {
		title?: string;
		description?: string;
		submitting?: boolean;
		onSubmit?: LoyerFormSubmit;
	} = $props();

	let idBien = $state('');
	let idLocataire = $state('');
	let dateLoyer = $state(new Date().toISOString().slice(0, 10));
	let montant = $state('');
	let statut = $state<LoyerStatus>('paye');

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		const payload = buildLoyerPayload({
			idBien,
			idLocataire,
			dateLoyer,
			montant,
			statut
		});
		if (!payload) {
			return;
		}

		const result = await onSubmit(payload);

		if (result !== false) {
			idBien = '';
			idLocataire = '';
			montant = '';
			statut = 'paye';
		}
	}
</script>

<Card class="sci-section-card">
	<CardHeader>
		<CardTitle class="text-lg">{title}</CardTitle>
		<CardDescription>{description}</CardDescription>
	</CardHeader>
	<CardContent>
		<form class="grid gap-3 md:grid-cols-5" onsubmit={handleSubmit}>
			<label class="sci-field">
				<span class="sci-field-label">ID Bien</span>
				<Input bind:value={idBien} required placeholder="bien-001" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">ID Locataire</span>
				<Input bind:value={idLocataire} placeholder="loc-001" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Date</span>
				<Input bind:value={dateLoyer} required type="date" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Montant (€)</span>
				<Input bind:value={montant} required type="number" min="0" step="10" placeholder="1250" />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Statut</span>
				<select bind:value={statut} class="sci-select">
					<option value="paye">Payé</option>
					<option value="en_attente">En attente</option>
					<option value="en_retard">En retard</option>
				</select>
			</label>
			<div class="md:col-span-5 flex justify-end">
				<Button type="submit" disabled={submitting} class="min-w-[11rem]">
					{submitting ? 'Enregistrement...' : 'Ajouter le loyer'}
				</Button>
			</div>
		</form>
	</CardContent>
</Card>
