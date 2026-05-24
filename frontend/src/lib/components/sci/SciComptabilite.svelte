<script lang="ts">
	import { Wallet, BarChart3, Download, Loader2 } from 'lucide-svelte';
	import type { SCIDetail, ComptabiliteAnnuelle, ComptabiliteMoisItem } from '$lib/api';
	import { fetchComptabiliteAnnuelle, fetchComptabiliteMensuelle } from '$lib/api';
	import AnneeSelector from '$lib/components/AnneeSelector.svelte';
	import { formatEur } from '$lib/high-value/formatters';

	export let sciId: string;
	export let sci: SCIDetail;

	let comptaYear = new Date().getFullYear();
	let comptaView: 'annuel' | 'mensuel' = 'annuel';
	
	let comptaData: ComptabiliteAnnuelle | null = null;
	let comptaLoading = false;
	let comptaError = '';

	let mensuelData: ComptabiliteMoisItem[] = [];
	let mensuelLoading = false;
	let mensuelError = '';

	const MOIS_LABELS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'];

	$: mensuelMax = Math.max(1, ...mensuelData.map(m => Math.max(m.revenus, m.charges)));
	$: totalRevMensuel = mensuelData.reduce((s, m) => s + m.revenus, 0);
	$: totalChgMensuel = mensuelData.reduce((s, m) => s + m.charges, 0);

	$: if (comptaView === 'annuel') {
		loadComptabilite(comptaYear);
	} else {
		loadMensuel(comptaYear);
	}

	async function loadComptabilite(annee: number) {
		comptaLoading = true;
		comptaError = '';
		try {
			comptaData = await fetchComptabiliteAnnuelle(sciId, annee);
		} catch (err: any) {
			comptaError = err?.message ?? 'Impossible de charger la comptabilité.';
			comptaData = null;
		} finally {
			comptaLoading = false;
		}
	}

	async function loadMensuel(annee: number) {
		mensuelLoading = true;
		mensuelError = '';
		try {
			mensuelData = await fetchComptabiliteMensuelle(sciId, annee);
		} catch (err: any) {
			mensuelError = err?.message ?? 'Impossible de charger les données mensuelles.';
			mensuelData = [];
		} finally {
			mensuelLoading = false;
		}
	}

	function handleComptaYearChange(year: number) {
		comptaYear = year;
	}

	function formatVariation(value: number | null | undefined): { text: string; color: string } | null {
		if (value == null || value === 0) return null;
		const pct = Math.round(value);
		return {
			text: pct > 0 ? `+${pct}%` : `${pct}%`,
			color: pct > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
		};
	}

	$: comptaVarRevenus = comptaData ? formatVariation(comptaData.variation_n1?.revenus) : null;
	$: comptaVarCharges = comptaData ? formatVariation(comptaData.variation_n1?.charges) : null;
	$: comptaVarResultat = comptaData ? formatVariation(comptaData.variation_n1?.resultat) : null;

	function exportComptaCsv() {
		if (!comptaData) return;
		const headers = ['Bien', 'Revenus', 'Charges', 'Événements', 'Résultat'];
		const rows = (comptaData.biens || []).map(l => [
			l.adresse,
			l.revenus.toFixed(2),
			l.charges.toFixed(2),
			l.evenements_deductibles.toFixed(2),
			l.resultat.toFixed(2)
		]);
		rows.push([
			'TOTAL',
			comptaData.totaux?.revenus.toFixed(2),
			comptaData.totaux?.charges.toFixed(2),
			comptaData.totaux?.evenements_deductibles.toFixed(2),
			comptaData.totaux?.resultat.toFixed(2)
		]);
		const csvContent = [headers.join(';'), ...rows.map(r => r.join(';'))].join('\n');
		const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `comptabilite_${sci.nom}_${comptaYear}.csv`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}
</script>

<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div class="flex flex-wrap items-center gap-2">
			<Wallet class="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
			<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Comptabilité</h2>
			<AnneeSelector value={comptaYear} onchange={handleComptaYearChange} />
			<!-- Toggle Annuel / Mensuel -->
			<div class="ml-2 inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 dark:border-slate-700 dark:bg-slate-800" role="radiogroup" aria-label="Vue comptabilité">
				<button
					type="button"
					role="radio"
					aria-checked={comptaView === 'annuel'}
					on:click={() => { comptaView = 'annuel'; }}
					class="rounded-md px-3 py-1 text-xs font-medium transition-colors {comptaView === 'annuel'
						? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-slate-100'
						: 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
				>
					Annuel
				</button>
				<button
					type="button"
					role="radio"
					aria-checked={comptaView === 'mensuel'}
					on:click={() => { comptaView = 'mensuel'; }}
					class="inline-flex items-center gap-1 rounded-md px-3 py-1 text-xs font-medium transition-colors {comptaView === 'mensuel'
						? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-slate-100'
						: 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}"
				>
					<BarChart3 class="h-3 w-3" />
					Mensuel
				</button>
			</div>
		</div>
		{#if comptaView === 'annuel' && comptaData && (comptaData.biens || []).length > 0}
			<button
				type="button"
				on:click={exportComptaCsv}
				class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
			>
				<Download class="h-3.5 w-3.5" />
				Exporter (CSV)
			</button>
		{/if}
	</div>

	{#if comptaView === 'annuel'}
		<!-- Vue annuelle -->
		{#if comptaLoading}
			<div class="mt-4 flex items-center justify-center py-8">
				<Loader2 class="h-5 w-5 animate-spin text-slate-400" />
			</div>
		{:else if comptaError}
			<p class="mt-4 text-sm text-rose-600 dark:text-rose-400">{comptaError}</p>
		{:else if comptaData && (comptaData.biens || []).length > 0}
			<div class="mt-4 overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-slate-200 dark:border-slate-700">
							<th class="pb-2 text-left font-semibold text-slate-600 dark:text-slate-400">Bien</th>
							<th class="pb-2 text-right font-semibold text-slate-600 dark:text-slate-400">Revenus</th>
							<th class="pb-2 text-right font-semibold text-slate-600 dark:text-slate-400">Charges</th>
							<th class="pb-2 text-right font-semibold text-slate-600 dark:text-slate-400">Événements</th>
							<th class="pb-2 text-right font-semibold text-slate-600 dark:text-slate-400">Résultat</th>
						</tr>
					</thead>
					<tbody>
						{#each (comptaData.biens || []) as ligne}
							<tr class="border-b border-slate-100 dark:border-slate-800">
								<td class="py-2.5 font-medium text-slate-900 dark:text-slate-100">{ligne.adresse}</td>
								<td class="py-2.5 text-right text-slate-700 dark:text-slate-300">{formatEur(ligne.revenus)}</td>
								<td class="py-2.5 text-right text-slate-700 dark:text-slate-300">{formatEur(ligne.charges)}</td>
								<td class="py-2.5 text-right text-slate-700 dark:text-slate-300">{formatEur(ligne.evenements_deductibles)}</td>
								<td class="py-2.5 text-right font-semibold {ligne.resultat >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}">{formatEur(ligne.resultat)}</td>
							</tr>
						{/each}
					</tbody>
					<tfoot>
						<tr class="border-t-2 border-slate-300 dark:border-slate-600">
							<td class="pt-3 font-bold text-slate-900 dark:text-slate-100">Total</td>
							<td class="pt-3 text-right font-bold text-slate-900 dark:text-slate-100">
								{formatEur(comptaData.totaux?.revenus)}
								{#if comptaVarRevenus}<span class="ml-1 text-xs {comptaVarRevenus.color}">{comptaVarRevenus.text}</span>{/if}
							</td>
							<td class="pt-3 text-right font-bold text-slate-900 dark:text-slate-100">
								{formatEur(comptaData.totaux?.charges)}
								{#if comptaVarCharges}<span class="ml-1 text-xs {comptaVarCharges.color}">{comptaVarCharges.text}</span>{/if}
							</td>
							<td class="pt-3 text-right font-bold text-slate-900 dark:text-slate-100">
								{formatEur(comptaData.totaux?.evenements_deductibles)}
							</td>
							<td class="pt-3 text-right font-bold {comptaData.totaux?.resultat >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}">
								{formatEur(comptaData.totaux?.resultat)}
								{#if comptaVarResultat}<span class="ml-1 text-xs {comptaVarResultat.color}">{comptaVarResultat.text}</span>{/if}
							</td>
						</tr>
					</tfoot>
				</table>
			</div>
		{:else}
			<p class="mt-4 text-sm text-slate-500 dark:text-slate-400">Aucune donnée comptable pour {comptaYear}.</p>
		{/if}
	{:else}
		<!-- Vue mensuelle (graphique barres) -->
		{#if mensuelLoading}
			<div class="mt-4 flex items-center justify-center py-8">
				<Loader2 class="h-5 w-5 animate-spin text-slate-400" />
			</div>
		{:else if mensuelError}
			<p class="mt-4 text-sm text-rose-600 dark:text-rose-400">{mensuelError}</p>
		{:else if mensuelData.length > 0}
			<!-- Légende -->
			<div class="mt-4 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
				<span class="flex items-center gap-1.5">
					<span class="inline-block h-2.5 w-2.5 rounded-sm bg-emerald-500"></span>
					Revenus
				</span>
				<span class="flex items-center gap-1.5">
					<span class="inline-block h-2.5 w-2.5 rounded-sm bg-rose-400"></span>
					Charges
				</span>
			</div>
			<!-- Bar chart -->
			<div class="mt-3 flex items-end gap-1 overflow-x-auto pb-1" style="height: 160px;" role="img" aria-label="Graphique revenus vs charges mensuels {comptaYear}">
				{#each mensuelData as month, i}
					{@const revPct = mensuelMax > 0 ? (month.revenus / mensuelMax) * 100 : 0}
					{@const chgPct = mensuelMax > 0 ? (month.charges / mensuelMax) * 100 : 0}
					<div class="group relative flex flex-1 flex-col items-center gap-0.5" style="min-width: 40px;">
						<!-- Bars container -->
						<div class="flex w-full items-end justify-center gap-0.5" style="height: 130px;">
							<div
								class="w-3 rounded-t bg-emerald-500 transition-all duration-300 sm:w-4"
								style="height: {revPct}%; min-height: {month.revenus > 0 ? '4px' : '0px'};"
								title="Revenus {MOIS_LABELS[i]} : {formatEur(month.revenus)}"
							></div>
							<div
								class="w-3 rounded-t bg-rose-400 transition-all duration-300 sm:w-4"
								style="height: {chgPct}%; min-height: {month.charges > 0 ? '4px' : '0px'};"
								title="Charges {MOIS_LABELS[i]} : {formatEur(month.charges)}"
							></div>
						</div>
						<!-- Month label -->
						<span class="mt-1 text-[10px] font-medium text-slate-400 dark:text-slate-500">{MOIS_LABELS[i]}</span>
						<!-- Tooltip on hover -->
						<div class="pointer-events-none absolute -top-14 left-1/2 z-10 hidden -translate-x-1/2 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs shadow-lg group-hover:block dark:border-slate-700 dark:bg-slate-900">
							<p class="whitespace-nowrap font-medium text-slate-700 dark:text-slate-200">{MOIS_LABELS[i]} {comptaYear}</p>
							<p class="whitespace-nowrap text-emerald-600 dark:text-emerald-400">{formatEur(month.revenus)}</p>
							<p class="whitespace-nowrap text-rose-500 dark:text-rose-400">{formatEur(month.charges)}</p>
						</div>
					</div>
				{/each}
			</div>
			<!-- Monthly totals summary -->
			<div class="mt-3 flex flex-wrap items-center gap-4 border-t border-slate-100 pt-3 text-sm dark:border-slate-800">
				<span class="text-slate-500 dark:text-slate-400">
					Total revenus : <span class="font-semibold text-emerald-700 dark:text-emerald-300">{formatEur(totalRevMensuel)}</span>
				</span>
				<span class="text-slate-500 dark:text-slate-400">
					Total charges : <span class="font-semibold text-rose-700 dark:text-rose-300">{formatEur(totalChgMensuel)}</span>
				</span>
				<span class="text-slate-500 dark:text-slate-400">
					Résultat : <span class="font-semibold {totalRevMensuel - totalChgMensuel >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}">{formatEur(totalRevMensuel - totalChgMensuel)}</span>
				</span>
			</div>
		{:else}
			<p class="mt-4 text-sm text-slate-500 dark:text-slate-400">Aucune donnée mensuelle pour {comptaYear}.</p>
		{/if}
	{/if}
</div>
