<script lang="ts">
	import type { BailEmbed, RegularisationResult } from '$lib/api';
	import { fetchRegularisation, confirmRegularisation } from '$lib/api';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { Calculator, CheckCircle } from 'lucide-svelte';

	interface Props {
		bail: BailEmbed;
		sciId: string;
		bienId: string | number;
		isGerant: boolean;
		onRefresh: () => void;
	}

	let { bail, sciId, bienId, isGerant, onRefresh }: Props = $props();

	let showRegularisation = $state(false);
	let regularisationAnnee = $state(new Date().getFullYear() - 1);
	let regularisationLoading = $state(false);
	let regularisationResult = $state<RegularisationResult | null>(null);
	let regularisationConfirming = $state(false);
	let regularisationNotes = $state('');

	async function handleRegularisation() {
		if (!bail) return;
		regularisationLoading = true;
		regularisationResult = null;
		try {
			regularisationResult = await fetchRegularisation(
				sciId,
				String(bienId),
				String(bail.id),
				regularisationAnnee
			);
		} catch {
			addToast({ title: 'Erreur lors du calcul de la régularisation', variant: 'error' });
		} finally {
			regularisationLoading = false;
		}
	}

	async function handleConfirmRegularisation() {
		if (!bail || !regularisationResult) return;
		regularisationConfirming = true;
		try {
			await confirmRegularisation(
				sciId,
				String(bienId),
				String(bail.id),
				regularisationAnnee,
				regularisationNotes || undefined
			);
			addToast({ title: 'Régularisation confirmée', variant: 'success' });
			// Refresh to show saved status
			await handleRegularisation();
			regularisationNotes = '';
			onRefresh();
		} catch {
			addToast({ title: 'Erreur lors de la confirmation', variant: 'error' });
		} finally {
			regularisationConfirming = false;
		}
	}
</script>

{#if bail.statut === 'en_cours'}
	<div>
		<div class="flex items-center justify-between">
			<p class="text-xs font-medium text-slate-500 dark:text-slate-400">
				Régularisation des charges
			</p>
			{#if isGerant}
				<button
					onclick={() => { showRegularisation = !showRegularisation; }}
					class="inline-flex items-center gap-1.5 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300"
				>
					<Calculator class="h-3.5 w-3.5" />
					{showRegularisation ? 'Masquer' : 'Régulariser'}
				</button>
			{/if}
		</div>

		{#if showRegularisation}
			<div class="mt-3 rounded-xl border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-700 dark:bg-slate-900/50">
				<div class="flex items-end gap-3">
					<label class="block flex-1">
						<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Année</span>
						<select
							bind:value={regularisationAnnee}
							class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
						>
							{#each Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 1 - i) as annee (annee)}
								<option value={annee}>{annee}</option>
							{/each}
						</select>
					</label>
					<button
						onclick={handleRegularisation}
						disabled={regularisationLoading}
						class="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
					>
						<Calculator class="h-3.5 w-3.5" />
						{regularisationLoading ? 'Calcul...' : 'Calculer la régularisation'}
					</button>
				</div>

				{#if regularisationResult}
					<div class="mt-4 space-y-3">
						<div class="grid gap-3 sm:grid-cols-3">
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Provisions annuelles</p>
								<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{formatEur(regularisationResult.provisions_annuelles)}</p>
							</div>
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Charges réelles</p>
								<p class="mt-1 text-lg font-bold text-slate-900 dark:text-slate-100">{formatEur(regularisationResult.charges_reelles)}</p>
							</div>
							<div class="rounded-lg bg-white p-3 dark:bg-slate-800">
								<p class="text-xs font-medium text-slate-500 dark:text-slate-400">Solde</p>
								<p class="mt-1 text-lg font-bold {regularisationResult.solde > 0 ? 'text-emerald-600 dark:text-emerald-400' : regularisationResult.solde < 0 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-900 dark:text-slate-100'}">
									{formatEur(Math.abs(regularisationResult.solde))}
								</p>
							</div>
						</div>
						{#if regularisationResult.solde > 0}
							<div class="rounded-lg border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-800 dark:bg-emerald-950/30">
								<p class="text-sm font-medium text-emerald-800 dark:text-emerald-200">
									Le locataire a trop payé de {formatEur(regularisationResult.solde)}
								</p>
								<p class="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
									Un remboursement est dû au locataire.
								</p>
							</div>
						{:else if regularisationResult.solde < 0}
							<div class="rounded-lg border border-rose-200 bg-rose-50 p-3 dark:border-rose-800 dark:bg-rose-950/30">
								<p class="text-sm font-medium text-rose-800 dark:text-rose-200">
									Le locataire doit un complément de {formatEur(Math.abs(regularisationResult.solde))}
								</p>
								<p class="mt-1 text-xs text-rose-600 dark:text-rose-400">
									Un appel de régularisation peut être émis.
								</p>
							</div>
						{:else}
							<div class="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
								<p class="text-sm font-medium text-slate-700 dark:text-slate-300">
									Aucun écart — les provisions correspondent aux charges réelles.
								</p>
							</div>
						{/if}

						<!-- Saved status or confirm button -->
						{#if regularisationResult.saved?.statut === 'confirme'}
							<div class="rounded-lg border border-sky-200 bg-sky-50 p-3 dark:border-sky-800 dark:bg-sky-950/30">
								<div class="flex items-center gap-2">
									<CheckCircle class="h-4 w-4 text-sky-600 dark:text-sky-400" />
									<p class="text-sm font-medium text-sky-800 dark:text-sky-200">
										Régularisation confirmée le {formatFrDate(regularisationResult.saved.date_regularisation)}
									</p>
								</div>
								{#if regularisationResult.saved.notes}
									<p class="mt-1 text-xs text-sky-600 dark:text-sky-400">
										{regularisationResult.saved.notes}
									</p>
								{/if}
							</div>
						{:else if isGerant}
							<div class="space-y-3">
								<label class="block">
									<span class="text-xs font-medium text-slate-600 dark:text-slate-400">Notes (optionnel)</span>
									<input
										type="text"
										bind:value={regularisationNotes}
										placeholder="Ex : remboursement effectué par virement le..."
										class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
									/>
								</label>
								<button
									onclick={handleConfirmRegularisation}
									disabled={regularisationConfirming}
									class="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:opacity-50"
								>
									<CheckCircle class="h-3.5 w-3.5" />
									{regularisationConfirming ? 'Confirmation...' : 'Confirmer la régularisation'}
								</button>
							</div>
						{/if}

						<!-- Loi ALUR notice -->
						<p class="text-xs text-slate-400 dark:text-slate-500">
							Obligation annuelle (loi ALUR art. 23). Le bailleur doit régulariser au moins une fois par an.
						</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>
{/if}
