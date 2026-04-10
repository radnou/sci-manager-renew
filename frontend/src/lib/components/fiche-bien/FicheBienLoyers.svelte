<script lang="ts">
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { Plus, FileText, Check, Loader2, X, Filter, Mail } from 'lucide-svelte';
	import LockedAction from '$lib/components/LockedAction.svelte';
	import DatePopover from '$lib/components/ui/DatePopover.svelte';
	import {
		createLoyerForBien,
		updateLoyer,
		renderQuitus,
		sendQuittanceEmail,
		type EntityId,
		type LoyerCreatePayload,
		type LoyerStatus,
		type QuitusRequestPayload
	} from '$lib/api';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import Celebration from '$lib/components/Celebration.svelte';
	import DemoConversionPrompt from '$lib/components/DemoConversionPrompt.svelte';

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
		isDemo?: boolean;
	}

	let { loyers, isGerant, sciId, bienId, nomLocataire = '', nomSci = '', adresseBien = '', villeBien = '', onRefresh, isDemo = false }: Props = $props();

	let showCelebration = $state<{ type: 'checkmark' | 'badge' | 'confetti'; title: string; subtitle: string } | null>(null);
	let showConversionPrompt = $state(false);
	let conversionMessage = $state('');
	let showLoyerComposer = $state(false);
	let savingLoyer = $state(false);
	let payDateLoyerId: EntityId | null = $state(null);
	let payDateOpen = $state(false);
	let generatingQuittanceFor: string | null = $state(null);
	let sendingEmailFor: string | null = $state(null);
	let periode = $state(new Date().toISOString().slice(0, 7));
	let montant = $state(0);
	let statut = $state<LoyerStatus>('en_attente');

	// Loyer filters
	let loyerFilterStatus = $state('tous');
	let loyerFilterYear = $state('tous');

	function resetLoyerForm() {
		periode = new Date().toISOString().slice(0, 7);
		montant = 0;
		statut = 'en_attente';
	}

	function openLoyerComposer() {
		resetLoyerForm();
		showLoyerComposer = true;
	}

	function closeLoyerComposer() {
		showLoyerComposer = false;
	}

	async function handleCreateLoyer() {
		if (!periode || montant < 0) return;
		savingLoyer = true;
		try {
			const data: LoyerCreatePayload = {
				id_bien: bienId,
				date_loyer: `${periode}-01`,
				montant,
				statut
			};
			await createLoyerForBien(sciId, bienId, data);
			addToast({ title: 'Loyer enregistré', variant: 'success' });
			if (!localStorage.getItem('milestone_first_loyer')) {
				localStorage.setItem('milestone_first_loyer', 'true');
				showCelebration = {
					type: 'checkmark',
					title: 'Premier loyer enregistré !',
					subtitle: 'Votre suivi de trésorerie commence. GérerSCI calcule maintenant votre taux de recouvrement automatiquement.'
				};
			}
			closeLoyerComposer();
			onRefresh();
		} catch (err: any) {
			addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
		} finally {
			savingLoyer = false;
		}
	}

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
			const [year, month] = dateLoyer.split('-').map(Number);
			const date = new Date(year, month - 1, 15);
			return date.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
		} catch {
			return dateLoyer;
		}
	}

	// Loyer filter helpers
	const loyerYears = $derived(() => {
		const years = new Set<string>();
		for (const l of loyers) {
			if (l.date_loyer) years.add(String(l.date_loyer).slice(0, 4));
		}
		return [...years].sort().reverse();
	});

	const filteredLoyers = $derived(() => {
		return loyers.filter((l) => {
			if (loyerFilterStatus !== 'tous') {
				const s = l.statut ?? 'en_attente';
				if (loyerFilterStatus === 'en_retard' && s !== 'en_retard' && s !== 'retard') return false;
				if (loyerFilterStatus !== 'en_retard' && s !== loyerFilterStatus) return false;
			}
			if (loyerFilterYear !== 'tous') {
				if (!l.date_loyer || !String(l.date_loyer).startsWith(loyerFilterYear)) return false;
			}
			return true;
		});
	});

	const filteredLoyerTotal = $derived(() => {
		return filteredLoyers().reduce((sum: number, l: any) => sum + Number(l.montant ?? 0), 0);
	});

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
				variant: 'success',
				timeoutMs: 5000
			});
			if (!localStorage.getItem('milestone_first_quittance')) {
				localStorage.setItem('milestone_first_quittance', 'true');
				showCelebration = {
					type: 'badge',
					title: 'Quittance générée !',
					subtitle: 'Vos locataires reçoivent un document professionnel conforme. Fini les modèles Word.'
				};
			}
			if (isDemo) {
				const dismissed = localStorage.getItem('demo_prompt_dismissed');
				if (!dismissed || Date.now() - parseInt(dismissed) > 600000) {
					conversionMessage = 'Cette quittance a été générée avec des données de démonstration.';
					showConversionPrompt = true;
				}
			}
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

	async function handleSendEmail(loyer: any) {
		const filename = loyer.quittance_filename;
		if (!filename) {
			addToast({
				title: 'Quittance introuvable',
				description: "Générez d'abord la quittance avant de l'envoyer par email.",
				variant: 'error'
			});
			return;
		}

		sendingEmailFor = String(loyer.id);
		try {
			const result = await sendQuittanceEmail(filename, String(bienId));
			const emailMatch = result.message.match(/à (.+)$/);
			const emailDisplay = emailMatch ? emailMatch[1] : 'le locataire';
			addToast({
				title: 'Quittance envoyée',
				description: `Quittance envoyée à ${emailDisplay}.`,
				variant: 'success',
				timeoutMs: 5000
			});
		} catch (err: any) {
			addToast({
				title: "Erreur d'envoi",
				description: err?.message ?? "Impossible d'envoyer la quittance par email.",
				variant: 'error'
			});
		} finally {
			sendingEmailFor = null;
		}
	}
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Loyers</h2>
		{#if isGerant}
			{#if !showLoyerComposer}
				<LockedAction {isDemo} action="enregistrer un loyer">
					<button
						class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-sky-700"
						onclick={openLoyerComposer}
					>
						<Plus class="h-4 w-4" />
						Enregistrer un loyer
					</button>
				</LockedAction>
			{/if}
		{/if}
	</div>

	{#if isGerant && showLoyerComposer}
		<form
			class="mb-5 rounded-2xl border border-sky-200 bg-sky-50/60 p-4 dark:border-sky-900/60 dark:bg-sky-950/20"
			onsubmit={(event) => {
				event.preventDefault();
				handleCreateLoyer();
			}}
		>
			<div class="mb-3 flex items-start justify-between gap-3">
				<div>
					<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">Nouveau loyer</p>
					<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
						La saisie reste dans l'onglet Loyers, sans masquer les informations du bien.
					</p>
				</div>
				<button
					type="button"
					class="rounded-full border border-slate-300 p-2 text-slate-500 transition-colors hover:bg-white hover:text-slate-900 dark:border-slate-700 dark:hover:bg-slate-900 dark:hover:text-slate-100"
					onclick={closeLoyerComposer}
					aria-label="Fermer le formulaire de loyer"
				>
					<X class="h-4 w-4" />
				</button>
			</div>

			<div class="grid gap-4 md:grid-cols-3">
				<label class="block">
					<span class="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">P&eacute;riode</span>
					<input
						id="loyer-periode-inline"
						type="month"
						lang="fr"
						bind:value={periode}
						required
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
					/>
				</label>
				<label class="block">
					<span class="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">Montant (&euro;)</span>
					<input
						id="loyer-montant-inline"
						type="number"
						bind:value={montant}
						min="0"
						step="0.01"
						required
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
					/>
				</label>
				<div>
					<span class="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">Statut</span>
					<div class="flex flex-wrap gap-2" role="group" aria-label="Statut du loyer">
						{#each (['en_attente', 'paye', 'en_retard'] as const) as s}
							<button
								type="button"
								class="rounded-full px-3 py-1.5 text-xs font-medium transition-colors {statut === s ? 'bg-sky-600 text-white' : 'border border-slate-300 bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300'}"
								onclick={() => (statut = s)}
							>
								{s === 'paye' ? 'Payé' : s === 'en_attente' ? 'En attente' : 'En retard'}
							</button>
						{/each}
					</div>
				</div>
			</div>

			<div class="mt-4 flex justify-end gap-2">
				<button
					type="button"
					class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-white dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
					onclick={closeLoyerComposer}
				>
					Annuler
				</button>
				<button
					type="submit"
					disabled={savingLoyer}
					class="rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
				>
					{savingLoyer ? 'Enregistrement…' : 'Enregistrer'}
				</button>
			</div>
		</form>
	{/if}

	{#if loyers.length > 0}
		<!-- Loyer filters -->
		<div class="mb-4 flex flex-wrap items-center gap-3">
			<div class="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
				<Filter class="h-3.5 w-3.5" />
				Filtres
			</div>
			<select
				bind:value={loyerFilterStatus}
				class="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
				aria-label="Filtrer par statut"
			>
				<option value="tous">Tous les statuts</option>
				<option value="paye">Pay&eacute;</option>
				<option value="en_attente">En attente</option>
				<option value="en_retard">En retard</option>
			</select>
			<select
				bind:value={loyerFilterYear}
				class="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
				aria-label="Filtrer par année"
			>
				<option value="tous">Toutes les ann&eacute;es</option>
				{#each loyerYears() as year}
					<option value={year}>{year}</option>
				{/each}
			</select>
		</div>
	{/if}

	{#if loyers.length === 0}
		<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-12 dark:border-slate-700">
			<p class="text-sm text-slate-500 dark:text-slate-400">Aucun loyer enregistr&eacute; pour ce bien.</p>
			{#if isGerant}
				<p class="mt-1 text-xs text-slate-400 dark:text-slate-500">
					Cliquez sur &laquo; Enregistrer un loyer &raquo; pour commencer.
				</p>
			{/if}
		</div>
	{:else if filteredLoyers().length === 0}
		<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-8 dark:border-slate-700">
			<p class="text-sm text-slate-500 dark:text-slate-400">
				Aucun loyer ne correspond aux filtres s&eacute;lectionn&eacute;s.
			</p>
		</div>
	{:else}
		<div class="overflow-x-auto">
			<table class="w-full text-left text-sm">
				<thead>
					<tr class="border-b border-slate-200 dark:border-slate-700">
						<th class="pb-3 pr-4 text-xs font-medium text-slate-500 dark:text-slate-400">
							Mois
						</th>
						<th class="pb-3 pr-4 text-xs font-medium text-slate-500 dark:text-slate-400">
							Montant
						</th>
						<th class="pb-3 pr-4 text-xs font-medium text-slate-500 dark:text-slate-400">
							Statut
						</th>
						<th class="pb-3 pr-4 text-xs font-medium text-slate-500 dark:text-slate-400">
							Quittance
						</th>
						<th class="pb-3 pr-4 text-xs font-medium text-slate-500 dark:text-slate-400">
							Date paiement
						</th>
						{#if isGerant}
							<th class="pb-3 text-xs font-medium text-slate-500 dark:text-slate-400">
								Actions
							</th>
						{/if}
					</tr>
				</thead>
				<tbody>
					{#each filteredLoyers() as loyer (loyer.id ?? loyer.date_loyer)}
						{@const statut = getStatut(loyer.statut)}
						{@const isGenerating = generatingQuittanceFor === String(loyer.id)}
						{@const isSendingEmail = sendingEmailFor === String(loyer.id)}
						<tr class="border-b border-slate-100 last:border-0 dark:border-slate-800">
							<td class="py-3 pr-4 font-medium text-slate-900 dark:text-slate-100 capitalize">
								{buildPeriodeLabel(loyer.date_loyer)}
							</td>
							<td class="py-3 pr-4 text-slate-700 dark:text-slate-300">
								{formatEur(loyer.montant)}
							</td>
							<td class="py-3 pr-4">
								<span class="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium {statut.class}">
									{statut.label}
								</span>
							</td>
							<td class="py-3 pr-4">
								{#if loyer.statut === 'paye'}
									<button
										class="text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
										title="Générer la quittance"
										onclick={() => handleGenerateQuittance(loyer)}
									>
										<FileText class="h-4 w-4" />
									</button>
								{:else}
									<span class="text-slate-300 dark:text-slate-600">&mdash;</span>
								{/if}
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
										<LockedAction {isDemo} action="générer une quittance">
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
										</LockedAction>
										{#if loyer.statut === 'paye' && loyer.quittance_filename}
											<LockedAction {isDemo} action="envoyer une quittance par email">
												<button
													onclick={() => handleSendEmail(loyer)}
													disabled={isSendingEmail}
													class="inline-flex items-center gap-1 rounded-md border border-sky-200 bg-sky-50 px-2.5 py-1.5 text-xs font-medium text-sky-700 transition-colors hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-sky-800 dark:bg-sky-950/30 dark:text-sky-400"
													title="Envoyer par email au locataire"
												>
													{#if isSendingEmail}
														<Loader2 class="h-3 w-3 animate-spin" />
														Envoi…
													{:else}
														<Mail class="h-3 w-3" />
														Email
													{/if}
												</button>
											</LockedAction>
										{/if}
									</div>
								</td>
							{/if}
						</tr>
					{/each}
				</tbody>
				<tfoot>
					<tr class="border-t border-slate-200 dark:border-slate-700">
						<td class="py-3 pr-4 text-xs font-semibold text-slate-500 dark:text-slate-400">
							{filteredLoyers().length} loyer{filteredLoyers().length > 1 ? 's' : ''}
						</td>
						<td class="py-3 pr-4 font-semibold text-slate-900 dark:text-slate-100">
							{formatEur(filteredLoyerTotal())}
						</td>
						<td colspan={isGerant ? 4 : 3}></td>
					</tr>
				</tfoot>
			</table>
		</div>
	{/if}

</div>

{#if showCelebration}
	<Celebration
		type={showCelebration.type}
		title={showCelebration.title}
		subtitle={showCelebration.subtitle}
		onDismiss={() => { showCelebration = null; }}
	/>
{/if}

<DemoConversionPrompt
	message={conversionMessage}
	open={showConversionPrompt}
	onClose={() => { showConversionPrompt = false; }}
/>
