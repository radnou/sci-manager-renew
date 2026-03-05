<script lang="ts">
	import type { Bien, LoyerCreatePayload, LoyerStatus } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { buildLoyerPayload } from '$lib/high-value/loyers';

	type LoyerFormSubmit = (payload: LoyerCreatePayload) => Promise<boolean | void> | boolean | void;
	type BienOption = Pick<Bien, 'id' | 'adresse' | 'ville'>;

	let {
		title = 'Nouveau loyer',
		description = 'Enregistre un paiement mensuel pour un bien.',
		submitting = false,
		biens = [],
		onSubmit = () => true
	}: {
		title?: string;
		description?: string;
		submitting?: boolean;
		biens?: BienOption[];
		onSubmit?: LoyerFormSubmit;
	} = $props();

	let idBien = $state('');
	let idLocataire = $state('');
	let dateLoyer = $state(new Date().toISOString().slice(0, 10));
	let montant = $state('');
	let statut = $state<LoyerStatus>('paye');
	let selectedBien = $derived(
		biens.find((bien) => String(bien.id || '') === idBien)
	);

	$effect(() => {
		if (!idBien && biens.length > 0) {
			idBien = String(biens[0].id || '');
		}
	});

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (!idBien) {
			return;
		}

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
				<span class="sci-field-label">Bien</span>
				<select bind:value={idBien} class="sci-select" required disabled={biens.length === 0}>
					{#if biens.length === 0}
						<option value="">Aucun bien disponible</option>
					{:else}
						{#each biens as bien (bien.id)}
							<option value={String(bien.id || '')}>
								{bien.adresse} {bien.ville ? `- ${bien.ville}` : ''}
							</option>
						{/each}
					{/if}
				</select>
				{#if selectedBien}
					<span class="text-xs text-slate-500 dark:text-slate-400">
						Loyer rattache au bien selectionne.
					</span>
				{/if}
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
				<Button type="submit" disabled={submitting || biens.length === 0} class="min-w-[11rem]">
					{submitting ? 'Enregistrement...' : 'Ajouter le loyer'}
				</Button>
			</div>
		</form>
	</CardContent>
</Card>
