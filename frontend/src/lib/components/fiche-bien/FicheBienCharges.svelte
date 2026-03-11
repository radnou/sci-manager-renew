<script lang="ts">
	import type { AssurancePnoEmbed, FraisAgenceEmbed } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { Plus, Trash2, Shield, Building2 } from 'lucide-svelte';

	interface Props {
		charges: any[];
		assurancePno: AssurancePnoEmbed | null;
		fraisAgence: FraisAgenceEmbed[];
		isGerant: boolean;
		sciId: string;
		bienId: string | number;
	}

	let { charges, assurancePno, fraisAgence, isGerant, sciId, bienId }: Props = $props();

	const typeFraisLabels: Record<string, string> = {
		gestion_locative: 'Gestion locative',
		mise_en_location: 'Mise en location',
		autre: 'Autre'
	};

	function getFraisLabel(type: string): string {
		return typeFraisLabels[type] ?? type;
	}
</script>

<div class="space-y-6">
	<!-- D1: Charges -->
	<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="mb-4 flex items-center justify-between">
			<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Charges</h2>
			{#if isGerant}
				<button
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				>
					<Plus class="h-4 w-4" />
					Ajouter une charge
				</button>
			{/if}
		</div>

		{#if charges.length === 0}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700"
			>
				<p class="text-sm text-slate-500 dark:text-slate-400">
					Aucune charge enregistrée pour ce bien.
				</p>
				{#if isGerant}
					<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
						Cliquez sur "Ajouter une charge" pour commencer.
					</p>
				{/if}
			</div>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-slate-200 dark:border-slate-700">
							<th
								class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Libellé
							</th>
							<th
								class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Montant
							</th>
							<th
								class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Date
							</th>
							{#if isGerant}
								<th
									class="pb-3 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
								>
									Actions
								</th>
							{/if}
						</tr>
					</thead>
					<tbody>
						{#each charges as charge (charge.id ?? charge.date_paiement)}
							<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
								<td class="py-3 pr-4 font-medium text-slate-900 dark:text-slate-100">
									{charge.type_charge ?? charge.libelle ?? '—'}
								</td>
								<td class="py-3 pr-4 text-slate-700 dark:text-slate-300">
									{formatEur(charge.montant)}
								</td>
								<td class="py-3 pr-4 text-slate-500 dark:text-slate-400">
									{formatFrDate(charge.date_paiement ?? charge.date_charge)}
								</td>
								{#if isGerant}
									<td class="py-3">
										<button
											class="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700 transition-colors hover:bg-rose-100 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-400"
											title="Supprimer"
										>
											<Trash2 class="h-3 w-3" />
											Supprimer
										</button>
									</td>
								{/if}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>

	<!-- D2: Assurance PNO -->
	<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="mb-4 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<Shield class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Assurance PNO</h2>
			</div>
			{#if isGerant && !assurancePno}
				<button
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				>
					<Plus class="h-4 w-4" />
					Ajouter
				</button>
			{/if}
		</div>

		{#if assurancePno}
			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Assureur</p>
					<p class="mt-1 text-sm font-medium text-slate-900 dark:text-slate-100">
						{assurancePno.assureur}
					</p>
				</div>
				<div>
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						N° contrat
					</p>
					<p class="mt-1 text-sm text-slate-700 dark:text-slate-300">
						{assurancePno.numero_contrat ?? '—'}
					</p>
				</div>
				<div>
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">
						Prime annuelle
					</p>
					<p class="mt-1 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{formatEur(assurancePno.prime_annuelle)}
					</p>
				</div>
				<div>
					<p class="text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Période</p>
					<p class="mt-1 text-sm text-slate-700 dark:text-slate-300">
						{formatFrDate(assurancePno.date_debut)}
						{#if assurancePno.date_fin}
							— {formatFrDate(assurancePno.date_fin)}
						{/if}
					</p>
				</div>
			</div>
			{#if isGerant}
				<div class="mt-4 flex gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
					<button
						class="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
					>
						Modifier
					</button>
					<button
						class="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700 transition-colors hover:bg-rose-100 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-400"
					>
						<Trash2 class="h-3 w-3" />
						Supprimer
					</button>
				</div>
			{/if}
		{:else}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-8 dark:border-slate-700"
			>
				<Shield class="mb-2 h-8 w-8 text-slate-300 dark:text-slate-600" />
				<p class="text-sm text-slate-500 dark:text-slate-400">
					Aucune assurance PNO renseignée.
				</p>
			</div>
		{/if}
	</div>

	<!-- D3: Frais agence -->
	<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="mb-4 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<Building2 class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Frais d'agence</h2>
			</div>
			{#if isGerant}
				<button
					class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				>
					<Plus class="h-4 w-4" />
					Ajouter
				</button>
			{/if}
		</div>

		{#if fraisAgence.length === 0}
			<div
				class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-8 dark:border-slate-700"
			>
				<Building2 class="mb-2 h-8 w-8 text-slate-300 dark:text-slate-600" />
				<p class="text-sm text-slate-500 dark:text-slate-400">Aucun frais d'agence enregistré.</p>
			</div>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full text-left text-sm">
					<thead>
						<tr class="border-b border-slate-200 dark:border-slate-700">
							<th
								class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Type
							</th>
							<th
								class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Montant
							</th>
							<th
								class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Date
							</th>
							<th
								class="pb-3 pr-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
							>
								Description
							</th>
							{#if isGerant}
								<th
									class="pb-3 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase"
								>
									Actions
								</th>
							{/if}
						</tr>
					</thead>
					<tbody>
						{#each fraisAgence as frais (frais.id)}
							<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
								<td class="py-3 pr-4 font-medium text-slate-900 dark:text-slate-100">
									{getFraisLabel(frais.type_frais)}
								</td>
								<td class="py-3 pr-4 text-slate-700 dark:text-slate-300">
									{formatEur(frais.montant)}
								</td>
								<td class="py-3 pr-4 text-slate-500 dark:text-slate-400">
									{formatFrDate(frais.date_frais)}
								</td>
								<td class="py-3 pr-4 text-slate-500 dark:text-slate-400">
									{frais.description ?? '—'}
								</td>
								{#if isGerant}
									<td class="py-3">
										<button
											class="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700 transition-colors hover:bg-rose-100 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-400"
											title="Supprimer"
										>
											<Trash2 class="h-3 w-3" />
											Supprimer
										</button>
									</td>
								{/if}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>
