<script lang="ts">
	import type { FicheBien } from '$lib/api';
	import { formatEur } from '$lib/high-value/formatters';

	interface Props {
		bien: FicheBien;
		isGerant: boolean;
	}

	let { bien, isGerant }: Props = $props();

	let editing = $state(false);

	function toggleEdit() {
		editing = !editing;
	}

	const fields: Array<{ label: string; value: string | number | null; suffix?: string }> = $derived([
		{ label: 'Adresse', value: bien.adresse },
		{ label: 'Ville', value: bien.ville },
		{ label: 'Code postal', value: bien.code_postal },
		{ label: 'Type de bien', value: bien.type_bien },
		{ label: 'Surface', value: bien.surface_m2, suffix: 'm²' },
		{ label: 'Nombre de pièces', value: bien.nb_pieces },
		{ label: 'Classe DPE', value: bien.dpe_classe?.toUpperCase() ?? null },
		{ label: "Prix d'acquisition", value: bien.prix_acquisition != null ? formatEur(bien.prix_acquisition) : null },
		{ label: 'Loyer', value: formatEur(bien.loyer), suffix: '/mois' },
		{ label: 'Charges', value: formatEur(bien.charges), suffix: '/mois' }
	]);
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Identité du bien</h2>
		{#if isGerant}
			<button
				onclick={toggleEdit}
				class="text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
			>
				{editing ? 'Annuler' : 'Modifier'}
			</button>
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

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
		{#each fields as field}
			<div>
				<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
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

	{#if bien.rentabilite}
		<div class="mt-6 border-t border-slate-200 pt-4 dark:border-slate-800">
			<h3 class="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-300">Rentabilité</h3>
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Brute</p>
					<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
						{bien.rentabilite.brute.toFixed(1)}%
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Nette</p>
					<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">
						{bien.rentabilite.nette.toFixed(1)}%
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Cashflow mensuel</p>
					<p class="mt-1 text-lg font-bold {bien.rentabilite.cashflow_mensuel >= 0 ? 'text-emerald-600' : 'text-rose-600'}">
						{formatEur(bien.rentabilite.cashflow_mensuel)}
					</p>
				</div>
				<div class="rounded-xl bg-slate-50 p-3 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Cashflow annuel</p>
					<p class="mt-1 text-lg font-bold {bien.rentabilite.cashflow_annuel >= 0 ? 'text-emerald-600' : 'text-rose-600'}">
						{formatEur(bien.rentabilite.cashflow_annuel)}
					</p>
				</div>
			</div>
		</div>
	{/if}
</div>
