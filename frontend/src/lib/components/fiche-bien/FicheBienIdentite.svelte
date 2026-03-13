<script lang="ts">
	import type { FicheBien } from '$lib/api';
	import { updateBien } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import { addToast } from '$lib/components/ui/toast/toast-store';

	interface Props {
		bien: FicheBien;
		isGerant: boolean;
		onRefresh?: () => void;
	}

	let { bien, isGerant, onRefresh }: Props = $props();

	let editing = $state(false);
	let saving = $state(false);

	// Editable form state — reset every time editing is toggled on
	let form = $state(initForm());

	function initForm() {
		return {
			adresse: bien.adresse ?? '',
			ville: bien.ville ?? '',
			code_postal: bien.code_postal ?? '',
			type_locatif: bien.type_locatif ?? 'nu',
			surface_m2: bien.surface_m2 ?? '',
			nb_pieces: bien.nb_pieces ?? '',
			dpe_classe: bien.dpe_classe ?? '',
			loyer_cc: bien.loyer_cc ?? 0,
			charges: bien.charges ?? 0,
			prix_acquisition: bien.prix_acquisition ?? ''
		};
	}

	function toggleEdit() {
		if (!editing) {
			form = initForm();
		}
		editing = !editing;
	}

	async function handleSave() {
		saving = true;
		try {
			await updateBien(bien.id, {
				adresse: form.adresse || undefined,
				ville: form.ville || undefined,
				code_postal: form.code_postal || undefined,
				type_locatif: (form.type_locatif as 'nu' | 'meuble' | 'mixte') || undefined,
				loyer_cc: Number(form.loyer_cc) || undefined,
				charges: Number(form.charges) || undefined,
				prix_acquisition: form.prix_acquisition !== '' ? Number(form.prix_acquisition) : null
			});
			addToast({ title: 'Bien mis à jour', variant: 'success' });
			editing = false;
			onRefresh?.();
		} catch (err: any) {
			addToast({ title: err?.message ?? 'Erreur lors de la mise à jour', variant: 'error' });
		} finally {
			saving = false;
		}
	}

	const DPE_OPTIONS = ['', 'A', 'B', 'C', 'D', 'E', 'F', 'G'];
	const TYPE_OPTIONS: Array<{ value: string; label: string }> = [
		{ value: 'nu', label: 'Nu' },
		{ value: 'meuble', label: 'Meublé' },
		{ value: 'mixte', label: 'Mixte' }
	];

	const readonlyFields: Array<{ label: string; value: string | number | null; suffix?: string }> =
		$derived([
			{ label: 'Adresse', value: bien.adresse },
			{ label: 'Ville', value: bien.ville },
			{ label: 'Code postal', value: bien.code_postal },
			{ label: 'Type de bien', value: bien.type_locatif },
			{ label: 'Surface', value: bien.surface_m2, suffix: 'm²' },
			{ label: 'Nombre de pièces', value: bien.nb_pieces },
			{ label: 'Classe DPE', value: bien.dpe_classe?.toUpperCase() ?? null },
			{
				label: "Prix d'acquisition",
				value: bien.prix_acquisition != null ? formatEur(bien.prix_acquisition) : null
			},
			{ label: 'Loyer', value: formatEur(bien.loyer_cc), suffix: '/mois' },
			{ label: 'Charges', value: formatEur(bien.charges), suffix: '/mois' }
		]);
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Identité du bien</h2>
		{#if isGerant}
			<div class="flex items-center gap-2">
				{#if editing}
					<button
						onclick={handleSave}
						disabled={saving}
						class="rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
					>
						{saving ? 'Enregistrement…' : 'Enregistrer'}
					</button>
				{/if}
				<button
					onclick={toggleEdit}
					disabled={saving}
					class="text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300 disabled:opacity-50"
				>
					{editing ? 'Annuler' : 'Modifier'}
				</button>
			</div>
		{/if}
	</div>

	{#if bien.photo_url}
		<div class="mb-6">
			<img
				src={bien.photo_url}
				alt="Photo du bien - {bien.adresse}"
				class="h-48 w-full rounded-xl object-cover"
			/>
		</div>
	{/if}

	{#if editing}
		<form
			onsubmit={(e) => {
				e.preventDefault();
				handleSave();
			}}
			class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
		>
			<!-- Adresse -->
			<div class="sm:col-span-2 lg:col-span-3">
				<label for="edit-adresse" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Adresse
				</label>
				<input
					id="edit-adresse"
					type="text"
					bind:value={form.adresse}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				/>
			</div>

			<!-- Ville -->
			<div>
				<label for="edit-ville" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Ville
				</label>
				<input
					id="edit-ville"
					type="text"
					bind:value={form.ville}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				/>
			</div>

			<!-- Code postal -->
			<div>
				<label for="edit-cp" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Code postal
				</label>
				<input
					id="edit-cp"
					type="text"
					bind:value={form.code_postal}
					maxlength="5"
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				/>
			</div>

			<!-- Type de bien -->
			<div>
				<label for="edit-type" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Type de bien
				</label>
				<select
					id="edit-type"
					bind:value={form.type_locatif}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				>
					{#each TYPE_OPTIONS as opt}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>

			<!-- Surface -->
			<div>
				<label for="edit-surface" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Surface (m²)
				</label>
				<input
					id="edit-surface"
					type="number"
					step="0.01"
					min="0"
					bind:value={form.surface_m2}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				/>
			</div>

			<!-- Nombre de pièces -->
			<div>
				<label for="edit-pieces" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Nombre de pièces
				</label>
				<input
					id="edit-pieces"
					type="number"
					step="1"
					min="0"
					bind:value={form.nb_pieces}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				/>
			</div>

			<!-- DPE -->
			<div>
				<label for="edit-dpe" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Classe DPE
				</label>
				<select
					id="edit-dpe"
					bind:value={form.dpe_classe}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				>
					{#each DPE_OPTIONS as dpe}
						<option value={dpe}>{dpe || '—'}</option>
					{/each}
				</select>
			</div>

			<!-- Prix d'acquisition -->
			<div>
				<label for="edit-prix" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Prix d'acquisition (€)
				</label>
				<input
					id="edit-prix"
					type="number"
					step="0.01"
					min="0"
					bind:value={form.prix_acquisition}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				/>
			</div>

			<!-- Loyer CC -->
			<div>
				<label for="edit-loyer" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Loyer CC (€/mois)
				</label>
				<input
					id="edit-loyer"
					type="number"
					step="0.01"
					min="0"
					bind:value={form.loyer_cc}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				/>
			</div>

			<!-- Charges -->
			<div>
				<label for="edit-charges" class="block text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Charges (€/mois)
				</label>
				<input
					id="edit-charges"
					type="number"
					step="0.01"
					min="0"
					bind:value={form.charges}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				/>
			</div>
		</form>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each readonlyFields as field}
				<div>
					<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
						{field.label}
					</p>
					<p class="mt-1 text-sm font-medium text-slate-900 dark:text-slate-100">
						{#if field.value != null}
							{field.value}{#if field.suffix}{' '}{field.suffix}{/if}
						{:else}
							<span class="text-slate-400">—</span>
						{/if}
					</p>
				</div>
			{/each}
		</div>
	{/if}

	{#if bien.rentabilite}
		<div class="mt-6 border-t border-slate-200 pt-4 dark:border-slate-800">
			<h3 class="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">Rentabilité</h3>
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">Brute</p>
					<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
						{bien.rentabilite.brute.toFixed(1)}%
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">Nette</p>
					<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
						{bien.rentabilite.nette.toFixed(1)}%
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">Cashflow mensuel</p>
					<p class="mt-1 text-lg font-bold {bien.rentabilite.cashflow_mensuel >= 0 ? 'text-emerald-600' : 'text-rose-600'}">
						{formatEur(bien.rentabilite.cashflow_mensuel)}
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">Cashflow annuel</p>
					<p class="mt-1 text-lg font-bold {bien.rentabilite.cashflow_annuel >= 0 ? 'text-emerald-600' : 'text-rose-600'}">
						{formatEur(bien.rentabilite.cashflow_annuel)}
					</p>
				</div>
			</div>
		</div>
	{/if}
</div>
