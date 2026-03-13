<script lang="ts">
	import { getContext } from 'svelte';
	import { Building2, MapPin, Landmark, Scale, Loader2, ArrowLeft } from 'lucide-svelte';
	import { invalidateAll } from '$app/navigation';
	import type { SCIDetail } from '$lib/api';
	import { updateSci } from '$lib/api';
	import { addToast } from '$lib/components/ui/toast';

	const sci = getContext<SCIDetail>('sci');
	const sciId = getContext<string>('sciId');
	const userRole = getContext<string>('userRole');

	const isGerant = $derived(userRole === 'gerant');

	// Form state — pre-filled from SCI context
	let nom = $state(sci.nom ?? '');
	let siren = $state(sci.siren ?? '');
	let dateCreation = $state(sci.date_creation ?? '');
	let objetSocial = $state(sci.objet_social ?? '');
	let adresseSiege = $state(sci.adresse_siege ?? '');
	let rcsVille = $state(sci.rcs_ville ?? '');
	let capitalSocial = $state<string>(sci.capital_social != null ? String(sci.capital_social) : '');
	let regimeFiscal = $state<'IR' | 'IS'>((sci.regime_fiscal as 'IR' | 'IS') ?? 'IR');

	let saving = $state(false);

	async function handleSave() {
		if (!nom.trim()) {
			addToast({ title: 'Erreur', description: 'Le nom de la SCI est obligatoire.', variant: 'error' });
			return;
		}
		saving = true;
		try {
			await updateSci(sciId, {
				nom: nom.trim(),
				siren: siren.trim() || null,
				regime_fiscal: regimeFiscal,
				adresse_siege: adresseSiege.trim() || null,
				date_creation: dateCreation || null,
				capital_social: capitalSocial ? parseFloat(capitalSocial) : null,
				objet_social: objetSocial.trim() || null,
				rcs_ville: rcsVille.trim() || null
			});
			await invalidateAll();
			addToast({ title: 'SCI modifiée', description: 'Les informations ont été mises à jour.', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de modifier la SCI.', variant: 'error' });
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head><title>Paramètres — {sci.nom} | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<div class="flex items-center gap-3">
			<a
				href="/scis/{sciId}"
				class="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400 dark:hover:bg-slate-800"
				aria-label="Retour à la vue d'ensemble"
			>
				<ArrowLeft class="h-4 w-4" />
			</a>
			<div>
				<p class="sci-eyebrow">Paramètres</p>
				<h1 class="sci-page-title">{sci.nom}</h1>
			</div>
		</div>
	</header>

	{#if !isGerant}
		<div class="rounded-2xl border border-amber-200 bg-amber-50 p-5 dark:border-amber-800 dark:bg-amber-950/20">
			<p class="text-sm font-medium text-amber-800 dark:text-amber-200">
				Seul le gérant peut modifier les paramètres de la SCI.
			</p>
		</div>
	{/if}

	<form
		onsubmit={(e) => { e.preventDefault(); handleSave(); }}
		class="space-y-6"
	>
		<!-- Section 1: Identité -->
		<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center gap-2 mb-5">
				<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-50 dark:bg-sky-950/40">
					<Building2 class="h-4 w-4 text-sky-600 dark:text-sky-400" />
				</div>
				<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Identité</h2>
			</div>
			<div class="grid gap-4 sm:grid-cols-2">
				<div class="sm:col-span-2">
					<label for="sci-nom" class="mb-1.5 block text-xs font-medium uppercase text-slate-500 dark:text-slate-400">
						Nom de la SCI <span class="text-rose-500">*</span>
					</label>
					<input
						id="sci-nom"
						type="text"
						bind:value={nom}
						required
						disabled={!isGerant}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 transition-colors focus:border-sky-500 focus:ring-1 focus:ring-sky-500 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:disabled:bg-slate-900 dark:disabled:text-slate-500"
					/>
				</div>
				<div>
					<label for="sci-siren" class="mb-1.5 block text-xs font-medium uppercase text-slate-500 dark:text-slate-400">
						SIREN
					</label>
					<input
						id="sci-siren"
						type="text"
						bind:value={siren}
						maxlength="9"
						pattern="\d{9}"
						placeholder="123456789"
						disabled={!isGerant}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 transition-colors focus:border-sky-500 focus:ring-1 focus:ring-sky-500 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:disabled:bg-slate-900 dark:disabled:text-slate-500"
					/>
				</div>
				<div>
					<label for="sci-date-creation" class="mb-1.5 block text-xs font-medium uppercase text-slate-500 dark:text-slate-400">
						Date de création
					</label>
					<input
						id="sci-date-creation"
						type="date"
						bind:value={dateCreation}
						disabled={!isGerant}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 transition-colors focus:border-sky-500 focus:ring-1 focus:ring-sky-500 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:disabled:bg-slate-900 dark:disabled:text-slate-500"
					/>
				</div>
				<div class="sm:col-span-2">
					<label for="sci-objet-social" class="mb-1.5 block text-xs font-medium uppercase text-slate-500 dark:text-slate-400">
						Objet social
					</label>
					<textarea
						id="sci-objet-social"
						bind:value={objetSocial}
						rows="3"
						placeholder="Acquisition, administration et gestion de biens immobiliers..."
						disabled={!isGerant}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 transition-colors focus:border-sky-500 focus:ring-1 focus:ring-sky-500 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:disabled:bg-slate-900 dark:disabled:text-slate-500"
					></textarea>
				</div>
			</div>
		</div>

		<!-- Section 2: Siège social -->
		<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center gap-2 mb-5">
				<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-50 dark:bg-purple-950/40">
					<MapPin class="h-4 w-4 text-purple-600 dark:text-purple-400" />
				</div>
				<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Siège social</h2>
			</div>
			<div class="grid gap-4 sm:grid-cols-2">
				<div class="sm:col-span-2">
					<label for="sci-adresse-siege" class="mb-1.5 block text-xs font-medium uppercase text-slate-500 dark:text-slate-400">
						Adresse du siège
					</label>
					<input
						id="sci-adresse-siege"
						type="text"
						bind:value={adresseSiege}
						placeholder="12 rue de Rivoli, 75001 Paris"
						disabled={!isGerant}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 transition-colors focus:border-sky-500 focus:ring-1 focus:ring-sky-500 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:disabled:bg-slate-900 dark:disabled:text-slate-500"
					/>
				</div>
				<div>
					<label for="sci-rcs-ville" class="mb-1.5 block text-xs font-medium uppercase text-slate-500 dark:text-slate-400">
						RCS Ville
					</label>
					<input
						id="sci-rcs-ville"
						type="text"
						bind:value={rcsVille}
						placeholder="Paris"
						disabled={!isGerant}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 transition-colors focus:border-sky-500 focus:ring-1 focus:ring-sky-500 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:disabled:bg-slate-900 dark:disabled:text-slate-500"
					/>
				</div>
			</div>
		</div>

		<!-- Section 3: Capital & Fiscal -->
		<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center gap-2 mb-5">
				<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 dark:bg-emerald-950/40">
					<Landmark class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
				</div>
				<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Capital & Fiscal</h2>
			</div>
			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<label for="sci-capital-social" class="mb-1.5 block text-xs font-medium uppercase text-slate-500 dark:text-slate-400">
						Capital social (EUR)
					</label>
					<input
						id="sci-capital-social"
						type="number"
						bind:value={capitalSocial}
						min="0"
						step="0.01"
						placeholder="1 000"
						disabled={!isGerant}
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 transition-colors focus:border-sky-500 focus:ring-1 focus:ring-sky-500 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:disabled:bg-slate-900 dark:disabled:text-slate-500"
					/>
				</div>
				<fieldset>
					<legend class="mb-1.5 block text-xs font-medium uppercase text-slate-500 dark:text-slate-400">
						Régime fiscal
					</legend>
					<div class="flex gap-2 mt-0.5">
						{#each (['IR', 'IS'] as const) as rf}
							<button
								type="button"
								disabled={!isGerant}
								class="rounded-full px-5 py-2 text-sm font-medium transition-colors {regimeFiscal === rf
									? 'bg-sky-600 text-white shadow-sm'
									: 'border border-slate-300 text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-400 dark:hover:bg-slate-800'} disabled:cursor-not-allowed disabled:opacity-50"
								onclick={() => regimeFiscal = rf}
							>
								{rf}
							</button>
						{/each}
					</div>
				</fieldset>
			</div>
		</div>

		<!-- Save button -->
		{#if isGerant}
			<div class="flex items-center justify-end gap-3 pt-2">
				<a
					href="/scis/{sciId}"
					class="rounded-lg px-5 py-2.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
				>
					Annuler
				</a>
				<button
					type="submit"
					disabled={saving}
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-sky-700 disabled:opacity-50"
				>
					{#if saving}<Loader2 class="h-4 w-4 animate-spin" />{/if}
					Enregistrer
				</button>
			</div>
		{/if}
	</form>
</section>
