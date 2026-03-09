<script lang="ts">
	import type {
		Bien,
		Locataire,
		Loyer,
		LoyerCreatePayload,
		LoyerStatus,
		LoyerUpdatePayload
	} from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { buildLoyerPayload, buildLoyerUpdatePayload } from '$lib/high-value/loyers';

	type LoyerFormMode = 'create' | 'edit';
	type LoyerFormSubmit = (
		payload: LoyerCreatePayload | LoyerUpdatePayload
	) => Promise<boolean | void> | boolean | void;
	type BienOption = Pick<Bien, 'id' | 'adresse' | 'ville'>;
	type LocataireOption = Pick<Locataire, 'id' | 'id_bien' | 'nom' | 'email'>;

	let {
		title = 'Nouveau loyer',
		description = 'Enregistre un paiement mensuel pour un bien.',
		mode = 'create',
		submitLabel = 'Ajouter le loyer',
		cancelLabel = 'Annuler',
		submitting = false,
		biens = [],
		locataires = [],
		initialValues = null,
		showBienField = true,
		showLocataireField = true,
		lockedBienLabel = '',
		onCancel = undefined,
		onSubmit = () => true
	}: {
		title?: string;
		description?: string;
		mode?: LoyerFormMode;
		submitLabel?: string;
		cancelLabel?: string;
		submitting?: boolean;
		biens?: BienOption[];
		locataires?: LocataireOption[];
		initialValues?: Loyer | null;
		showBienField?: boolean;
		showLocataireField?: boolean;
		lockedBienLabel?: string;
		onCancel?: (() => void) | undefined;
		onSubmit?: LoyerFormSubmit;
	} = $props();

	let idBien = $state('');
	let idLocataire = $state('');
	let dateLoyer = $state(new Date().toISOString().slice(0, 10));
	let montant = $state('');
	let statut = $state<LoyerStatus>('paye');
	let formElement: HTMLFormElement | null = null;
	let selectedBien = $derived(biens.find((bien) => String(bien.id || '') === idBien));
	let availableLocataires = $derived(
		locataires.filter((locataire) => {
			if (!idBien) {
				return true;
			}

			return String(locataire.id_bien || '') === idBien;
		})
	);
	let lastAppliedLoyerKey = $state('');

	function resetFormFields() {
		idBien = '';
		idLocataire = '';
		dateLoyer = new Date().toISOString().slice(0, 10);
		montant = '';
		statut = 'paye';
	}

	function applyLoyerValues(loyer: Loyer) {
		idBien = String(loyer.id_bien || '');
		idLocataire = String(loyer.id_locataire || '');
		dateLoyer = loyer.date_loyer || new Date().toISOString().slice(0, 10);
		montant = loyer.montant != null ? String(loyer.montant) : '';
		statut = (loyer.statut as LoyerStatus) || 'paye';
	}

	$effect(() => {
		if (mode === 'edit') {
			return;
		}

		if (!idBien && biens.length > 0) {
			idBien = String(biens[0].id || '');
		}
	});

	$effect(() => {
		if (!showLocataireField) {
			return;
		}

		if (availableLocataires.length === 0) {
			idLocataire = '';
			return;
		}

		if (!availableLocataires.some((locataire) => String(locataire.id || '') === idLocataire)) {
			idLocataire = String(availableLocataires[0].id || '');
		}
	});

	$effect(() => {
		if (mode !== 'edit' || !initialValues) {
			lastAppliedLoyerKey = '';
			return;
		}

		const nextKey = String(
			initialValues.id || `${initialValues.id_bien}-${initialValues.date_loyer}`
		);
		if (lastAppliedLoyerKey === nextKey) {
			return;
		}

		applyLoyerValues(initialValues);
		lastAppliedLoyerKey = nextKey;
	});

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		if (mode === 'create' && !idBien) {
			return;
		}

		if (showLocataireField && !idLocataire) {
			return;
		}

		const formInput = {
			idBien,
			idLocataire,
			dateLoyer,
			montant,
			statut
		};
		const payload =
			mode === 'edit' ? buildLoyerUpdatePayload(formInput) : buildLoyerPayload(formInput);
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
		<form bind:this={formElement} class="grid gap-3 md:grid-cols-5" onsubmit={handleSubmit}>
			{#if showBienField}
				<label class="sci-field" for="loyer-bien">
					<span class="sci-field-label">Bien</span>
					<select
						id="loyer-bien"
						name="loyer-bien"
						bind:value={idBien}
						class="sci-select"
						required
						disabled={biens.length === 0}
					>
						{#if biens.length === 0}
							<option value="">Aucun bien disponible</option>
						{:else}
							{#each biens as bien (bien.id)}
								<option value={String(bien.id || '')}>
									{bien.adresse}
									{bien.ville ? `- ${bien.ville}` : ''}
								</option>
							{/each}
						{/if}
					</select>
					{#if selectedBien}
						<span class="text-xs text-slate-500 dark:text-slate-400">
							Loyer rattaché au bien sélectionné.
						</span>
					{/if}
				</label>
			{:else}
				<div class="sci-field">
					<span class="sci-field-label">Bien concerné</span>
					<div
						class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					>
						{lockedBienLabel ||
							(selectedBien
								? `${selectedBien.adresse}${selectedBien.ville ? ` - ${selectedBien.ville}` : ''}`
								: 'Bien sélectionné')}
					</div>
				</div>
			{/if}
			{#if showLocataireField}
				<label class="sci-field" for="loyer-reference-locataire">
					<span class="sci-field-label">Locataire</span>
					<select
						id="loyer-reference-locataire"
						name="loyer-reference-locataire"
						bind:value={idLocataire}
						class="sci-select"
						required
						disabled={availableLocataires.length === 0}
					>
						{#if availableLocataires.length === 0}
							<option value="">Aucun locataire disponible</option>
						{:else}
							{#each availableLocataires as locataire (locataire.id)}
								<option value={String(locataire.id || '')}>
									{locataire.nom}
									{locataire.email ? ` - ${locataire.email}` : ''}
								</option>
							{/each}
						{/if}
					</select>
					{#if availableLocataires.length === 0}
						<span class="text-xs text-slate-500 dark:text-slate-400">
							Ajoute d’abord le locataire dans le module `Locataires`.
						</span>
					{:else}
						<span class="text-xs text-slate-500 dark:text-slate-400">
							Le flux sera rattaché au locataire référencé pour le suivi et la quittance.
						</span>
					{/if}
				</label>
			{/if}
			<label class="sci-field" for="loyer-date">
				<span class="sci-field-label">Date</span>
				<Input id="loyer-date" name="loyer-date" bind:value={dateLoyer} required type="date" />
			</label>
			<label class="sci-field" for="loyer-montant">
				<span class="sci-field-label">Montant (€)</span>
				<Input
					id="loyer-montant"
					name="loyer-montant"
					bind:value={montant}
					required
					type="number"
					min="0"
					step="10"
					placeholder="1250"
				/>
			</label>
			<label class="sci-field" for="loyer-statut">
				<span class="sci-field-label">Statut</span>
				<select id="loyer-statut" name="loyer-statut" bind:value={statut} class="sci-select">
					<option value="paye">Payé</option>
					<option value="en_attente">En attente</option>
					<option value="en_retard">En retard</option>
				</select>
			</label>
			<div class="flex justify-end gap-2 md:col-span-5">
				{#if mode === 'edit' && onCancel}
					<Button type="button" variant="outline" onclick={onCancel}>
						{cancelLabel}
					</Button>
				{/if}
				<Button
					type="button"
					disabled={submitting || (mode === 'create' && biens.length === 0)}
					class="min-w-[11rem]"
					onclick={() => {
						formElement?.requestSubmit();
					}}
				>
					{submitting ? 'Enregistrement...' : submitLabel}
				</Button>
			</div>
		</form>
	</CardContent>
</Card>
