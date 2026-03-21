<script lang="ts">
	import { Plus, Trash2, Loader2, Calendar, Tag, User, Coins } from 'lucide-svelte';
	import {
		fetchEvenements,
		createEvenement,
		deleteEvenement,
		type Evenement,
		type EvenementType,
		type EntityId
	} from '$lib/api';
	import { addToast } from '$lib/components/ui/toast';

	interface Props {
		sciId: string;
		bienId: string;
		isGerant: boolean;
	}

	let { sciId, bienId, isGerant }: Props = $props();

	let evenements = $state<Evenement[]>([]);
	let loading = $state(true);
	let showForm = $state(false);
	let submitting = $state(false);
	let deletingId = $state<EntityId | null>(null);

	// Form fields
	let formType = $state<EvenementType>('reparation');
	let formTitre = $state('');
	let formDate = $state(new Date().toISOString().slice(0, 10));
	let formMontant = $state<string>('');
	let formPrestataire = $state('');
	let formDeductible = $state(false);

	const typeOptions: { value: EvenementType; label: string }[] = [
		{ value: 'reparation', label: 'Réparation' },
		{ value: 'travaux', label: 'Travaux' },
		{ value: 'sinistre', label: 'Sinistre' },
		{ value: 'visite', label: 'Visite' },
		{ value: 'controle', label: 'Contrôle' },
		{ value: 'diagnostic', label: 'Diagnostic' },
		{ value: 'autre', label: 'Autre' }
	];

	const typeBadgeColors: Record<EvenementType, string> = {
		reparation: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
		travaux: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
		sinistre: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300',
		visite: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
		controle: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
		diagnostic: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
		autre: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
	};

	function typeLabel(type: EvenementType): string {
		return typeOptions.find(o => o.value === type)?.label ?? type;
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('fr-FR', {
			day: 'numeric',
			month: 'long',
			year: 'numeric'
		});
	}

	function formatEur(value: number): string {
		return new Intl.NumberFormat('fr-FR', {
			style: 'currency',
			currency: 'EUR',
			maximumFractionDigits: 0
		}).format(value);
	}

	$effect(() => {
		loadEvenements();
	});

	async function loadEvenements() {
		loading = true;
		try {
			evenements = await fetchEvenements(sciId, bienId);
		} catch {
			evenements = [];
		} finally {
			loading = false;
		}
	}

	function resetForm() {
		formType = 'reparation';
		formTitre = '';
		formDate = new Date().toISOString().slice(0, 10);
		formMontant = '';
		formPrestataire = '';
		formDeductible = false;
		showForm = false;
	}

	async function handleSubmit() {
		if (!formTitre.trim()) {
			addToast({ title: 'Titre requis', description: 'Veuillez saisir un titre.', variant: 'error' });
			return;
		}
		submitting = true;
		try {
			const data = {
				type_evenement: formType,
				titre: formTitre.trim(),
				date_evenement: formDate,
				montant: formMontant ? parseFloat(formMontant) : null,
				prestataire: formPrestataire.trim() || null,
				deductible_fiscal: formDeductible
			};
			const created = await createEvenement(sciId, bienId, data);
			evenements = [created, ...evenements];
			resetForm();
			addToast({ title: 'Événement ajouté', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? "Impossible de créer l'événement.", variant: 'error' });
		} finally {
			submitting = false;
		}
	}

	async function handleDelete(eventId: EntityId) {
		deletingId = eventId;
		try {
			await deleteEvenement(sciId, bienId, eventId);
			evenements = evenements.filter(e => e.id !== eventId);
			addToast({ title: 'Événement supprimé', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? "Impossible de supprimer l'événement.", variant: 'error' });
		} finally {
			deletingId = null;
		}
	}
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Événements</h2>
		{#if isGerant && !showForm}
			<button
				type="button"
				onclick={() => { showForm = true; }}
				class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
			>
				<Plus class="h-4 w-4" />
				Ajouter un événement
			</button>
		{/if}
	</div>

	<!-- Inline form -->
	{#if showForm && isGerant}
		<div class="rounded-xl border border-sky-200 bg-sky-50/50 p-4 dark:border-sky-900 dark:bg-sky-950/20">
			<div class="grid gap-3 sm:grid-cols-2">
				<div>
					<label for="evt-type" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Type</label>
					<select
						id="evt-type"
						bind:value={formType}
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					>
						{#each typeOptions as opt}
							<option value={opt.value}>{opt.label}</option>
						{/each}
					</select>
				</div>
				<div>
					<label for="evt-titre" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Titre</label>
					<input
						id="evt-titre"
						type="text"
						bind:value={formTitre}
						placeholder="Ex: Remplacement chaudière"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
				<div>
					<label for="evt-date" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Date</label>
					<input
						id="evt-date"
						type="date"
						lang="fr"
						bind:value={formDate}
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
				<div>
					<label for="evt-montant" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Montant (optionnel)</label>
					<input
						id="evt-montant"
						type="number"
						step="0.01"
						bind:value={formMontant}
						placeholder="0.00"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
				<div>
					<label for="evt-prestataire" class="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">Prestataire (optionnel)</label>
					<input
						id="evt-prestataire"
						type="text"
						bind:value={formPrestataire}
						placeholder="Ex: Plombier Martin"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
					/>
				</div>
				<div class="flex items-end">
					<label class="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
						<input type="checkbox" bind:checked={formDeductible} class="rounded border-slate-300" />
						Déductible fiscalement
					</label>
				</div>
			</div>
			<div class="mt-4 flex items-center gap-2">
				<button
					type="button"
					onclick={handleSubmit}
					disabled={submitting}
					class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
				>
					{#if submitting}<Loader2 class="h-4 w-4 animate-spin" />{/if}
					Enregistrer
				</button>
				<button
					type="button"
					onclick={resetForm}
					disabled={submitting}
					class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
				>
					Annuler
				</button>
			</div>
		</div>
	{/if}

	<!-- Timeline -->
	{#if loading}
		<div class="flex items-center justify-center py-8">
			<Loader2 class="h-5 w-5 animate-spin text-slate-400" />
		</div>
	{:else if evenements.length === 0}
		<div class="rounded-xl border border-dashed border-slate-300 bg-slate-50 py-10 text-center dark:border-slate-700 dark:bg-slate-900">
			<Calendar class="mx-auto h-8 w-8 text-slate-300 dark:text-slate-600" />
			<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">Aucun événement enregistré pour ce bien.</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each evenements as evt (evt.id)}
				<div class="flex items-start gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-950">
					<!-- Date column -->
					<div class="flex-shrink-0 text-center">
						<p class="text-xs font-medium text-slate-400 dark:text-slate-500">
							{new Date(evt.date_evenement).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
						</p>
						<p class="text-xs text-slate-400 dark:text-slate-500">
							{new Date(evt.date_evenement).getFullYear()}
						</p>
					</div>

					<!-- Content -->
					<div class="min-w-0 flex-1">
						<div class="flex flex-wrap items-center gap-2">
							<span class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium {typeBadgeColors[evt.type_evenement] ?? typeBadgeColors['autre']}">
								{typeLabel(evt.type_evenement)}
							</span>
							<span class="text-sm font-medium text-slate-900 dark:text-slate-100">{evt.titre}</span>
							{#if evt.deductible_fiscal}
								<span class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">Déductible</span>
							{/if}
						</div>
						<div class="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
							{#if evt.montant != null}
								<span class="inline-flex items-center gap-1">
									<Coins class="h-3 w-3" />
									{formatEur(evt.montant)}
								</span>
							{/if}
							{#if evt.prestataire}
								<span class="inline-flex items-center gap-1">
									<User class="h-3 w-3" />
									{evt.prestataire}
								</span>
							{/if}
						</div>
					</div>

					<!-- Delete -->
					{#if isGerant}
						<button
							type="button"
							onclick={() => handleDelete(evt.id)}
							disabled={deletingId === evt.id}
							class="flex-shrink-0 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/30 dark:hover:text-rose-400"
							title="Supprimer"
						>
							{#if deletingId === evt.id}
								<Loader2 class="h-4 w-4 animate-spin" />
							{:else}
								<Trash2 class="h-4 w-4" />
							{/if}
						</button>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
