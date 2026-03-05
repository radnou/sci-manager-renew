<script lang="ts">
	import { onDestroy } from 'svelte';
	import type { Bien, Loyer } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { downloadQuitus, generateQuitus as generateQuitusApi } from '$lib/api';
	import { mapBienTypeLabel } from '$lib/high-value/biens';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';

	type GenerateQuitusFn = () => Promise<Blob>;

	let {
		title = 'Quittance PDF',
		description = 'Prépare une quittance à partir d’un loyer sélectionné, sans exposer les identifiants techniques.',
		buttonLabel = 'Générer le PDF',
		loyers = [],
		biens = [],
		generateQuitus = undefined
	}: {
		title?: string;
		description?: string;
		buttonLabel?: string;
		loyers?: Loyer[];
		biens?: Bien[];
		generateQuitus?: GenerateQuitusFn;
	} = $props();

	let selectedLoyerId = $state('');
	let nomLocataire = $state('Locataire à confirmer');
	let periode = $state('');
	let montant = $state('1200');
	let pdfUrl = $state('');
	let pdfDownloadName = $state('quittance.pdf');
	let isLoading = $state(false);
	let errorMessage = $state('');

	let selectedLoyer = $derived(
		loyers.find((loyer) => String(loyer.id || '') === selectedLoyerId) || null
	);
	let selectedBien = $derived(
		selectedLoyer
			? biens.find((bien) => String(bien.id || '') === String(selectedLoyer.id_bien || '')) || null
			: null
	);

	function buildLoyerOptionLabel(loyer: Loyer) {
		const bien = biens.find((entry) => String(entry.id || '') === String(loyer.id_bien || ''));
		const bienLabel = bien
			? bien.ville
				? `${bien.adresse} • ${bien.ville}`
				: bien.adresse
			: 'Bien non identifié';
		return `${formatFrDate(loyer.date_loyer)} • ${bienLabel} • ${formatEur(loyer.montant)}`;
	}

	$effect(() => {
		if (!selectedLoyerId && loyers.length > 0) {
			selectedLoyerId = String(loyers[0].id || '');
		}
	});

	$effect(() => {
		if (!selectedLoyer) {
			return;
		}

		periode = formatFrDate(selectedLoyer.date_loyer, 'Période à confirmer');
		montant = String(selectedLoyer.montant ?? 0);
		pdfDownloadName = `quittance-${String(selectedLoyer.id || 'document')}.pdf`;
	});

	async function defaultGenerateQuitus() {
		if (!selectedLoyer || !selectedBien) {
			throw new Error('Sélectionne un loyer rattaché à un bien avant de générer la quittance.');
		}

		const generated = await generateQuitusApi({
			id_loyer: String(selectedLoyer.id || ''),
			id_bien: String(selectedBien.id || ''),
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
			if (blob.size === 0 || (blob.type && !blob.type.toLowerCase().includes('pdf'))) {
				throw new Error('Le document généré n’est pas un PDF exploitable.');
			}
			if (pdfUrl) {
				URL.revokeObjectURL(pdfUrl);
			}
			pdfUrl = URL.createObjectURL(blob);
		} catch (error) {
			errorMessage = formatApiErrorMessage(error, 'Erreur inattendue lors de la génération');
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
		{#if loyers.length === 0}
			<div
				class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
			>
				Aucun loyer disponible. Enregistre d’abord un encaissement pour préparer une quittance.
			</div>
		{:else}
			<div class="grid gap-3">
				<label class="sci-field" for="quitus-loyer">
					<span class="sci-field-label">Loyer concerné</span>
					<select
						id="quitus-loyer"
						name="quitus-loyer"
						class="sci-select"
						bind:value={selectedLoyerId}
					>
						{#each loyers as loyer (String(loyer.id || `${loyer.id_bien}-${loyer.date_loyer}`))}
							<option value={String(loyer.id || '')}>{buildLoyerOptionLabel(loyer)}</option>
						{/each}
					</select>
				</label>

				{#if selectedBien}
					<div
						class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					>
						<p class="font-semibold">{selectedBien.adresse}</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							{selectedBien.ville || 'Ville non renseignée'} • {mapBienTypeLabel(
								selectedBien.type_locatif
							)}
						</p>
					</div>
				{/if}

				<label class="sci-field" for="quitus-locataire">
					<span class="sci-field-label">Locataire</span>
					<Input id="quitus-locataire" bind:value={nomLocataire} placeholder="Nom du locataire" />
				</label>
				<label class="sci-field" for="quitus-periode">
					<span class="sci-field-label">Période</span>
					<Input id="quitus-periode" bind:value={periode} />
				</label>
				<label class="sci-field" for="quitus-montant">
					<span class="sci-field-label">Montant</span>
					<Input id="quitus-montant" bind:value={montant} type="number" min="0" step="10" />
				</label>
				<Button onclick={handleGenerate} disabled={isLoading} class="w-full">
					{isLoading ? 'Génération…' : buttonLabel}
				</Button>
			</div>
		{/if}

		{#if errorMessage}
			<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
		{/if}

		{#if pdfUrl}
			<div
				class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900"
			>
				<div>
					<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">Document généré</p>
					<p class="text-sm text-slate-500 dark:text-slate-400">
						Prévisualise le document ci-dessous ou télécharge-le directement.
					</p>
				</div>
				<div class="flex flex-wrap gap-2">
					<a href={pdfUrl} download={pdfDownloadName}>
						<Button variant="outline" size="sm">Télécharger</Button>
					</a>
					<a href={pdfUrl} target="_blank" rel="noreferrer">
						<Button size="sm">Ouvrir dans un onglet</Button>
					</a>
				</div>
			</div>

			<object
				data={pdfUrl}
				type="application/pdf"
				class="h-[28rem] w-full rounded-xl border border-slate-200 bg-white"
				aria-label="Prévisualisation de la quittance"
			>
				<div
					class="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100"
				>
					<p class="font-semibold">Prévisualisation indisponible dans ce navigateur.</p>
					<p class="mt-2">Le PDF a bien été généré, mais son rendu intégré a échoué.</p>
					<div class="mt-4">
						<a href={pdfUrl} download={pdfDownloadName}>
							<Button size="sm">Télécharger la quittance</Button>
						</a>
					</div>
				</div>
			</object>
		{:else}
			<div class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
				<p class="text-sm font-medium text-slate-700">Aucun document généré.</p>
				<p class="mt-1 text-sm text-slate-500">
					Sélectionne un loyer puis génère une quittance prête à être envoyée.
				</p>
			</div>
		{/if}
	</CardContent>
</Card>
