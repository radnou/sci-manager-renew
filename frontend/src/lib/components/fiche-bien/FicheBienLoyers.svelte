<script lang="ts">
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { Plus, FileText, Check, Loader2 } from 'lucide-svelte';
	import LoyerModal from '$lib/components/fiche-bien/modals/LoyerModal.svelte';
	import DatePopover from '$lib/components/ui/DatePopover.svelte';
	import { updateLoyer, renderQuitus, type EntityId, type QuitusRequestPayload } from '$lib/api';
	import { addToast } from '$lib/components/ui/toast/toast-store';

	interface Props {
		loyers: Array<any>;
		isGerant: boolean;
		sciId: string | number;
		bienId: string | number;
		nomLocataire?: string;
		nomSci?: string;
		adresseBien?: string;
		villeBien?: string;
		onRefresh: () => void;
	}

	let { loyers, isGerant, sciId, bienId, nomLocataire = '', nomSci = '', adresseBien = '', villeBien = '', onRefresh }: Props = $props();

	let showLoyerModal = $state(false);
	let payDateLoyerId: EntityId | null = $state(null);
	let payDateOpen = $state(false);
	let generatingQuittanceFor: string | null = $state(null);

	async function handleMarkPaid(date: string) {
		if (!payDateLoyerId) return;
		try {
			await updateLoyer(payDateLoyerId, { statut: 'paye', date_paiement: date });
			addToast({ title: 'Loyer marqué payé', variant: 'success' });
			payDateLoyerId = null;
			onRefresh();
		} catch (err: any) {
			addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
		}
	}

	const statutConfig: Record<string, { label: string; class: string }> = {
		paye: {
			label: 'Payé',
			class: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
		},
		en_attente: {
			label: 'En attente',
			class: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
		},
		en_retard: {
			label: 'En retard',
			class: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
		},
		retard: {
			label: 'En retard',
			class: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
		}
	};

	function getStatut(statut: string | null | undefined) {
		if (!statut) return statutConfig['en_attente'];
		return statutConfig[statut] ?? { label: statut, class: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' };
	}

	function buildPeriodeLabel(dateLoyer: string): string {
		try {
			const date = new Date(dateLoyer);
			return date.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
		} catch {
			return dateLoyer;
		}
	}

	async function handleGenerateQuittance(loyer: any) {
		if (!loyer.id || !nomLocataire) {
			addToast({
				title: 'Données manquantes',
				description: 'Le locataire ou le loyer est introuvable. Vérifiez le bail actif.',
				variant: 'error'
			});
			return;
		}

		const loyerId = String(loyer.id);
		generatingQuittanceFor = loyerId;

		try {
			const payload: QuitusRequestPayload = {
				id_loyer: loyerId,
				id_bien: String(bienId),
				nom_locataire: nomLocataire,
				periode: buildPeriodeLabel(loyer.date_loyer),
				montant: loyer.montant,
				nom_sci: nomSci || undefined,
				adresse_bien: adresseBien || undefined,
				ville_bien: villeBien || undefined
			};

			const blob = await renderQuitus(payload);
			const url = URL.createObjectURL(blob);
			window.open(url, '_blank');

			setTimeout(() => URL.revokeObjectURL(url), 30_000);

			addToast({
				title: 'Quittance générée',
				description: `Quittance pour ${buildPeriodeLabel(loyer.date_loyer)} ouverte dans un nouvel onglet.`,
				variant: 'success'
			});
		} catch (err: any) {
			const message = err?.message ?? 'Impossible de générer la quittance.';
			addToast({
				title: 'Erreur de génération',
				description: message,
				variant: 'error'
			});
		} finally {
			generatingQuittanceFor = null;
		}
	}
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Loyers</h2>
		{#if isGerant}
			<button
				class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				onclick={() => showLoyerModal = true}
			>
				<Plus class="h-4 w-4" />
				Enregistrer un loyer
			</button>
		{/if}
	</div>

	{#if loyers.length === 0}
		<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700">
			<p class="text-sm text-slate-500 dark:text-slate-400">Aucun loyer enregistré pour ce bien.</p>
			{#if isGerant}
				<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
					Cliquez sur "Enregistrer un loyer" pour commencer.
				</p>
			{/if}
		</div>
	{:else}
		<div class="overflow-x-auto">
			<table class="w-full text-left text-sm">
				<thead>
					<tr class="border-b border-slate-200 dark:border-slate-700">
						<th class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
							Mois
						</th>
						<th class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
							Montant
						</th>
						<th class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
							Statut
						</th>
						<th class="pb-3 pr-4 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
							Date paiement
						</th>
						{#if isGerant}
							<th class="pb-3 text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
								Actions
							</th>
						{/if}
					</tr>
				</thead>
				<tbody>
					{#each loyers as loyer (loyer.id ?? loyer.date_loyer)}
						{@const statut = getStatut(loyer.statut)}
						{@const isGenerating = generatingQuittanceFor === String(loyer.id)}
						<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
							<td class="py-3 pr-4 font-medium text-slate-900 dark:text-slate-100">
								{formatFrDate(loyer.date_loyer)}
							</td>
							<td class="py-3 pr-4 text-slate-700 dark:text-slate-300">
								{formatEur(loyer.montant)}
							</td>
							<td class="py-3 pr-4">
								<span class="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium {statut.class}">
									{statut.label}
								</span>
							</td>
							<td class="py-3 pr-4 text-slate-500 dark:text-slate-400">
								{loyer.date_paiement ? formatFrDate(loyer.date_paiement) : '—'}
							</td>
							{#if isGerant}
								<td class="py-3">
									<div class="flex gap-2">
										{#if loyer.statut !== 'paye'}
											<div class="relative">
												<button
													class="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-2.5 py-1.5 text-xs font-medium text-emerald-700 transition-colors hover:bg-emerald-100 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400"
													title="Marquer comme payé"
													onclick={() => { payDateLoyerId = loyer.id; payDateOpen = true; }}
												>
													<Check class="h-3 w-3" />
													Payé
												</button>
												{#if payDateOpen && payDateLoyerId === loyer.id}
													<DatePopover
														bind:open={payDateOpen}
														onconfirm={(d) => handleMarkPaid(d)}
														oncancel={() => { payDateOpen = false; payDateLoyerId = null; }}
													/>
												{/if}
											</div>
										{/if}
										<button
											onclick={() => handleGenerateQuittance(loyer)}
											disabled={isGenerating}
											class="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400"
											title="Générer la quittance"
										>
											{#if isGenerating}
												<Loader2 class="h-3 w-3 animate-spin" />
												Génération…
											{:else}
												<FileText class="h-3 w-3" />
												Quittance
											{/if}
										</button>
									</div>
								</td>
							{/if}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}

	<LoyerModal bind:open={showLoyerModal} {sciId} {bienId} defaultMontant={0} onSuccess={onRefresh} />
</div>
