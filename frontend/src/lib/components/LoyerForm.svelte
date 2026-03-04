<script lang="ts">
	import type { LoyerCreatePayload } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { buildLoyerPayload } from '$lib/high-value/loyers';

	type LoyerFormSubmit =
		| ((payload: LoyerCreatePayload) => Promise<boolean | void> | boolean | void)
		| undefined;

	export let title = 'Nouveau loyer';
	export let description = 'Enregistre un paiement mensuel pour un bien.';
	export let submitting = false;
	export let onSubmit: LoyerFormSubmit = () => true;

	let idBien = '';
	let dateLoyer = new Date().toISOString().slice(0, 10);
	let montant = '';
	let statut = 'paye';

	async function handleSubmit() {
		const payload = buildLoyerPayload({
			idBien,
			dateLoyer,
			montant,
			statut
		});
		if (!payload) {
			return;
		}

		const result = await onSubmit?.(payload);

		if (result !== false) {
			idBien = '';
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
		<form class="grid gap-3 md:grid-cols-4" on:submit|preventDefault={handleSubmit}>
			<label class="sci-field">
				<span class="sci-field-label">ID Bien</span>
				<Input bind:value={idBien} required placeholder="BIEN-001" />
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
					<option value="retard">Retard</option>
				</select>
			</label>
			<div class="md:col-span-4 flex justify-end">
				<Button type="submit" disabled={submitting} class="min-w-[11rem]">
					{submitting ? 'Enregistrement...' : 'Ajouter le loyer'}
				</Button>
			</div>
		</form>
	</CardContent>
</Card>
