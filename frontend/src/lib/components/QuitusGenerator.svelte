<script lang="ts">
	import { onDestroy } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';

	type GenerateQuitus = () => Promise<Blob>;

	export let title = 'Quittance PDF';
	export let description = 'Génère puis prévisualise le quittus directement dans l’interface.';
	export let buttonLabel = 'Générer le quittus';
	export let endpoint = '/v1/quitus';
	export let generateQuitus: GenerateQuitus | undefined = undefined;

	let pdfUrl = '';
	let isLoading = false;
	let errorMessage = '';

	async function defaultGenerateQuitus() {
		const res = await fetch(endpoint);
		if (!res.ok) {
			throw new Error(`Impossible de générer le quittus (HTTP ${res.status})`);
		}
		return res.blob();
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
	<CardHeader class="md:flex-row md:items-end md:justify-between">
		<div>
			<CardTitle class="text-lg">{title}</CardTitle>
			<CardDescription>{description}</CardDescription>
		</div>
		<Button onclick={handleGenerate} disabled={isLoading} class="min-w-[12rem]">
			{isLoading ? 'Génération…' : buttonLabel}
		</Button>
	</CardHeader>
	<CardContent class="space-y-3 pt-0">
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
