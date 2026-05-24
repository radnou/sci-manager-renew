<script lang="ts">
	import {
		updateNotificationPreferences,
		type NotificationPreference
	} from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { addToast } from '$lib/components/ui/toast';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import LockedAction from '$lib/components/LockedAction.svelte';

	interface Props {
		notifPreferences: NotificationPreference[];
		notifLoading: boolean;
		notifError: string;
		isDemo: boolean;
	}

	let { notifPreferences = $bindable(), notifLoading, notifError, isDemo }: Props = $props();

	let notifSaving = $state(false);

	const notificationTypeLabels: Record<string, string> = {
		late_payment: 'Loyer en retard',
		bail_expiring: 'Bail expirant',
		bail_renewal: 'Renouvellement de bail',
		bail_conge_deadline: 'Délai de congé bail',
		quittance_pending: 'Quittance en attente',
		pno_expiring: 'PNO expirant',
		new_loyer: 'Nouveau loyer',
		new_associe: 'Nouvel associé',
		subscription_expiring: 'Abonnement expirant',
		regularisation_charges: 'Régularisation de charges',
		fiscal_deadline: 'Échéance fiscale',
		irl_revision: 'Révision IRL (loyer)',
		avenant_bail: 'Avenant au bail',
		sinistre: 'Sinistre déclaré',
		system: 'Notification système'
	};

	async function handleNotifSave() {
		notifSaving = true;
		try {
			const result = await updateNotificationPreferences(notifPreferences);
			notifPreferences = result.preferences;
			addToast({
				title: 'Notifications mises à jour',
				description: 'Vos préférences de notification ont été enregistrées.',
				variant: 'success'
			});
		} catch (error) {
			addToast({
				title: 'Erreur',
				description: formatApiErrorMessage(
					error,
					'Impossible de sauvegarder les préférences de notification.'
				),
				variant: 'error'
			});
		} finally {
			notifSaving = false;
		}
	}

	function toggleEmailEnabled(index: number) {
		notifPreferences[index] = {
			...notifPreferences[index],
			email_enabled: !notifPreferences[index].email_enabled
		};
	}

	function toggleInAppEnabled(index: number) {
		notifPreferences[index] = {
			...notifPreferences[index],
			in_app_enabled: !notifPreferences[index].in_app_enabled
		};
	}
</script>

<div id="panel-notifications" role="tabpanel" aria-labelledby="tab-notifications">
	<Card class="sci-section-card">
		<CardHeader>
			<div>
				<CardTitle class="text-lg">Préférences de notification</CardTitle>
				<CardDescription>Configurez les types de notifications que vous souhaitez recevoir par email et dans l'application.</CardDescription>
			</div>
		</CardHeader>
		<CardContent class="space-y-4 pt-0">
			{#if notifLoading}
				<div class="flex items-center justify-center py-8">
					<div class="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900 dark:border-slate-600 dark:border-t-slate-100"></div>
					<span class="ml-3 text-sm text-slate-500 dark:text-slate-400">Chargement des préférences...</span>
				</div>
			{:else if notifError}
				<p class="sci-inline-alert sci-inline-alert-error">{notifError}</p>
			{:else}
				<div class="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-900">
								<th class="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-300">Type</th>
								<th class="px-4 py-3 text-center font-semibold text-slate-700 dark:text-slate-300">Email</th>
								<th class="px-4 py-3 text-center font-semibold text-slate-700 dark:text-slate-300">In-app</th>
							</tr>
						</thead>
						<tbody>
							{#each notifPreferences as pref, i (pref.type)}
								<tr class="border-b border-slate-100 last:border-b-0 dark:border-slate-800">
									<td class="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
										{notificationTypeLabels[pref.type] ?? pref.type}
									</td>
									<td class="px-4 py-3 text-center">
										<button
											type="button"
											role="switch"
											aria-checked={pref.email_enabled}
											aria-label={`Email pour ${notificationTypeLabels[pref.type] ?? pref.type}`}
											class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2 {pref.email_enabled ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}"
											onclick={() => toggleEmailEnabled(i)}
										>
											<span
												class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out {pref.email_enabled ? 'translate-x-5' : 'translate-x-0'}"
											></span>
										</button>
									</td>
									<td class="px-4 py-3 text-center">
										<button
											type="button"
											role="switch"
											aria-checked={pref.in_app_enabled}
											aria-label={`In-app pour ${notificationTypeLabels[pref.type] ?? pref.type}`}
											class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2 {pref.in_app_enabled ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}"
											onclick={() => toggleInAppEnabled(i)}
										>
											<span
												class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out {pref.in_app_enabled ? 'translate-x-5' : 'translate-x-0'}"
											></span>
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				<div class="flex items-center gap-3 pt-2">
					<LockedAction {isDemo} action="configurer les notifications">
						<Button onclick={handleNotifSave} disabled={notifSaving}>
							{notifSaving ? 'Enregistrement...' : 'Enregistrer les notifications'}
						</Button>
					</LockedAction>
				</div>
			{/if}
		</CardContent>
	</Card>
</div>
