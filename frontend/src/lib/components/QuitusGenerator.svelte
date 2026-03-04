<script lang="ts">
	import { onDestroy } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { downloadQuitus, generateQuitus as generateQuitusApi } from '$lib/api';

	type GenerateQuitusFn = () => Promise<Blob>;

	let {
		title = 'Quittance PDF',
		description = 'Génère puis prévisualise le quittus directement dans l’interface.',
		buttonLabel = 'Générer le quittus',
		generateQuitus = undefined
	}: {
		title?: string;
		description?: string;
		buttonLabel?: string;
		generateQuitus?: GenerateQuitusFn;
	} = $props();

	let idLoyer = $state('loyer-demo');
	let idBien = $state('bien-demo');
	let nomLocataire = $state('Locataire Demo');
	let periode = $state('Mars 2026');
	let montant = $state('1200');
	let pdfUrl = $state('');
	let isLoading = $state(false);
	let errorMessage = $state('');

	async function defaultGenerateQuitus() {
		const generated = await generateQuitusApi({
			id_loyer: idLoyer,
			id_bien: idBien,
			nom_locataire: nomLocataire,
			periode,
			montant: Number.parseFloat(montant)
		});

		return downloadQuitus(generated.pdf_url);
	}

	async function handleGenerate() {
		errorMessage = '';
		isLoading = true;

		try {
			const blob = await (generateQuitus ? generateQuitus() : defaultGenerateQuitus());
			if (pdfUrl) {
				URL.revokeObjectURL(pdfUrl);
			}
			pdfUrl = URL.createObjectURL(blob);
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Erreur inattendue lors de la génération';
		} finally {
			isLoading = false;
		}
	}

	onDestroy(() => {
		if (pdfUrl) {
			URL.revokeObjectURL(pdfUrl);
		}
	});
</script>

<Card class="sci-section-card">
	<CardHeader>
		<div>
			<CardTitle class="text-lg">{title}</CardTitle>
			<CardDescription>{description}</CardDescription>
		</div>
	</CardHeader>
	<CardContent class="space-y-3 pt-0">
		<div class="grid gap-3">
			<label class="sci-field">
				<span class="sci-field-label">ID Loyer</span>
				<Input bind:value={idLoyer} />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">ID Bien</span>
				<Input bind:value={idBien} />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Locataire</span>
				<Input bind:value={nomLocataire} />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Période</span>
				<Input bind:value={periode} />
			</label>
			<label class="sci-field">
				<span class="sci-field-label">Montant</span>
				<Input bind:value={montant} type="number" min="0" step="10" />
			</label>
			<Button onclick={handleGenerate} disabled={isLoading} class="w-full">
				{isLoading ? 'Génération…' : buttonLabel}
			</Button>
		</div>

		{#if errorMessage}
			<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
		{/if}

		{#if pdfUrl}
			<iframe
				src={pdfUrl}
				title="Prévisualisation quittus"
				class="h-[28rem] w-full rounded-xl border border-slate-200 bg-white"
			></iframe>
		{:else}
			<div class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
				<p class="text-sm font-medium text-slate-700">Aucun document généré.</p>
				<p class="mt-1 text-sm text-slate-500">Clique sur le bouton pour créer une quittance prête à être partagée.</p>
			</div>
		{/if}
	</CardContent>
</Card>
