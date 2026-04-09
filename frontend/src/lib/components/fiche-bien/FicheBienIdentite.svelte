<script lang="ts">
	import type { FicheBien } from '$lib/api';
	import { updateBien } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import FieldHint from '$lib/components/FieldHint.svelte';
	import LockedAction from '$lib/components/LockedAction.svelte';

	interface Props {
		bien: FicheBien;
		isGerant: boolean;
		onRefresh?: () => void;
		isDemo?: boolean;
	}

	let { bien, isGerant, onRefresh, isDemo = false }: Props = $props();

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
			type_bien: bien.type_bien ?? '',
			surface_m2: bien.surface_m2 ?? '',
			nb_pieces: bien.nb_pieces ?? '',
			dpe_classe: bien.dpe_classe ?? '',
			loyer_cc: bien.loyer_cc ?? 0,
			charges: bien.charges ?? 0,
			prix_acquisition: bien.prix_acquisition ?? '',
			jour_loyer: bien.jour_loyer ?? ('' as number | '')
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
				type_bien: form.type_bien || undefined,
				loyer_cc: Number(form.loyer_cc) || undefined,
				charges: Number(form.charges) || undefined,
				prix_acquisition: form.prix_acquisition !== '' ? Number(form.prix_acquisition) : null,
				jour_loyer: form.jour_loyer !== '' && form.jour_loyer != null ? Number(form.jour_loyer) : null
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

	const fieldHints: Record<string, string> = {
		surface_m2: 'Obligatoire pour le bail et le calcul de la taxe foncière. Loi Boutin pour les locations.',
		dpe_classe: 'Obligatoire dans toute annonce et bail depuis 2023. Les logements F et G sont progressivement interdits à la location.',
		prix_acquisition: 'Nécessaire pour calculer votre rentabilité et la plus-value en cas de revente. Frais de notaire inclus.',
		type_locatif: 'Détermine le régime fiscal applicable (micro-foncier vs réel) et les obligations déclaratives.',
		type_bien: "Permet d'adapter les calculs de charges et les obligations réglementaires."
	};

	const completenessFields = ['adresse', 'ville', 'code_postal', 'type_bien', 'type_locatif', 'surface_m2', 'nb_pieces', 'dpe_classe', 'prix_acquisition', 'loyer_cc'];

	const completeness = $derived.by(() => {
		if (!bien) return { filled: 0, total: completenessFields.length, percent: 0, missing: [] as string[] };
		let filled = 0;
		const missing: string[] = [];
		for (const f of completenessFields) {
			const val = (bien as any)[f];
			if (val !== null && val !== undefined && val !== '' && val !== 0) filled++;
			else missing.push(f);
		}
		return { filled, total: completenessFields.length, percent: Math.round((filled / completenessFields.length) * 100), missing };
	});

	const completenessColor = $derived(completeness.percent >= 80 ? 'bg-emerald-500' : completeness.percent >= 50 ? 'bg-amber-500' : 'bg-rose-500');

	const completenessMessage = $derived.by(() => {
		const m = completeness.missing;
		if (m.length === 0) return '';
		const labels: Record<string, string> = {
			dpe_classe: 'DPE', prix_acquisition: "prix d'acquisition", surface_m2: 'surface',
			type_locatif: 'type de location', type_bien: 'type de bien', loyer_cc: 'loyer',
			nb_pieces: 'nombre de pièces', adresse: 'adresse', ville: 'ville', code_postal: 'code postal'
		};
		const top = m.slice(0, 2).map(f => labels[f] || f);
		if (top.some(t => t === 'DPE' || t === "prix d'acquisition")) {
			return `Complétez le ${top.join(' et le ')} pour débloquer le calcul de rentabilité.`;
		}
		return `Complétez le ${top.join(' et le ')} pour enrichir votre fiche.`;
	});

	const DPE_OPTIONS = ['', 'A', 'B', 'C', 'D', 'E', 'F', 'G'];
	const TYPE_OPTIONS: Array<{ value: string; label: string }> = [
		{ value: 'nu', label: 'Location nue' },
		{ value: 'meuble', label: 'Meublé' },
		{ value: 'mixte', label: 'Mixte' }
	];

	const TYPE_BIEN_OPTIONS: Array<{ value: string; label: string }> = [
		{ value: 'appartement', label: 'Appartement' },
		{ value: 'maison', label: 'Maison' },
		{ value: 'immeuble', label: 'Immeuble' },
		{ value: 'local_commercial', label: 'Local commercial' },
		{ value: 'parking', label: 'Parking / Box' },
		{ value: 'autre', label: 'Autre' }
	];

	function formatTypeBien(value: string | null | undefined): string | null {
		if (!value) return null;
		const found = TYPE_BIEN_OPTIONS.find((o) => o.value === value);
		return found ? found.label : value;
	}

	function formatTypeLocatif(value: string | null | undefined): string | null {
		if (!value) return null;
		const found = TYPE_OPTIONS.find((o) => o.value === value);
		return found ? found.label : value;
	}

	const readonlyFields: Array<{ label: string; value: string | number | null; suffix?: string }> =
		$derived([
			{ label: 'Adresse', value: bien.adresse },
			{ label: 'Ville', value: bien.ville },
			{ label: 'Code postal', value: bien.code_postal },
			{ label: 'Type de bien', value: formatTypeBien(bien.type_bien) },
			{ label: 'Type de location', value: formatTypeLocatif(bien.type_locatif) },
			{ label: 'Surface', value: bien.surface_m2, suffix: 'm²' },
			{ label: 'Nombre de pièces', value: bien.nb_pieces },
			{ label: 'Classe DPE', value: bien.dpe_classe?.toUpperCase() ?? null },
			{
				label: "Prix d'acquisition",
				value: bien.prix_acquisition != null ? formatEur(bien.prix_acquisition) : null
			},
			{ label: 'Loyer', value: formatEur(bien.loyer_cc), suffix: '/mois' },
			{ label: 'Charges', value: formatEur(bien.charges), suffix: '/mois' },
			{
				label: 'Jour de loyer',
				value: bien.jour_loyer != null ? bien.jour_loyer : null,
				suffix: bien.jour_loyer != null ? 'du mois' : undefined
			}
		]);
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Identité du bien</h2>
		{#if isGerant}
			<LockedAction {isDemo} action="modifier ce bien">
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
			</LockedAction>
		{/if}
	</div>

	{#if completeness.percent < 100}
		<div class="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
			<div class="flex items-center justify-between text-sm">
				<span class="text-slate-600 dark:text-slate-400">Profil du bien : {completeness.filled}/{completeness.total} champs renseignés</span>
				<span class="font-medium text-slate-700 dark:text-slate-300">{completeness.percent}%</span>
			</div>
			<div class="mt-2 h-1.5 w-full rounded-full bg-slate-200 dark:bg-slate-700">
				<div class="h-full rounded-full transition-all duration-500 {completenessColor}" style="width: {completeness.percent}%"></div>
			</div>
			{#if completenessMessage}
				<p class="mt-2 text-xs text-slate-500 dark:text-slate-400">💡 {completenessMessage}</p>
			{/if}
		</div>
	{/if}

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
				<label for="edit-adresse" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
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
				<label for="edit-ville" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
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
				<label for="edit-cp" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
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
				<label for="edit-type-bien" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
					Type de bien <FieldHint text={fieldHints.type_bien} />
				</label>
				<select
					id="edit-type-bien"
					bind:value={form.type_bien}
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				>
					<option value="">—</option>
					{#each TYPE_BIEN_OPTIONS as opt}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>

			<!-- Type de location -->
			<div>
				<label for="edit-type" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
					Type de location <FieldHint text={fieldHints.type_locatif} />
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
				<label for="edit-surface" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
					Surface (m²) <FieldHint text={fieldHints.surface_m2} />
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
				<label for="edit-pieces" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
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
				<label for="edit-dpe" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
					Classe DPE <FieldHint text={fieldHints.dpe_classe} />
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
				<label for="edit-prix" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
					Prix d'acquisition (€) <FieldHint text={fieldHints.prix_acquisition} />
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
				<label for="edit-loyer" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
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
				<label for="edit-charges" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
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

			<!-- Jour de loyer -->
			<div>
				<label for="edit-jour-loyer" class="block text-xs font-medium text-slate-500 dark:text-slate-400">
					Jour de loyer <FieldHint text="Jour du mois (1-28) pour la génération automatique du loyer. Laissez vide pour hériter du réglage de la SCI." />
				</label>
				<input
					id="edit-jour-loyer"
					type="number"
					step="1"
					min="1"
					max="28"
					bind:value={form.jour_loyer}
					placeholder="Hérité de la SCI"
					class="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
				/>
			</div>
		</form>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each readonlyFields as field}
				<div>
					<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
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

	<!-- Rentabilité affichée uniquement dans l'onglet Rentabilité dédié -->
</div>
