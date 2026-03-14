<script lang="ts">
	import { onMount } from 'svelte';
	import {
		fetchSubscriptionEntitlements,
		fetchNotificationPreferences,
		updateNotificationPreferences,
		type SubscriptionEntitlements,
		type NotificationPreference
	} from '$lib/api';
	import WorkspaceActionBar from '$lib/components/WorkspaceActionBar.svelte';
	import WorkspaceHeader from '$lib/components/WorkspaceHeader.svelte';
	import WorkspaceRailCard from '$lib/components/WorkspaceRailCard.svelte';
	import { addToast } from '$lib/components/ui/toast';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import {
		DEFAULT_APPLICATION_PREFERENCES,
		readApplicationPreferences,
		saveApplicationPreferences,
		type ApplicationLandingRoute,
		type ApplicationPreferences
	} from '$lib/settings/application-preferences';

	const landingRouteOptions: Array<{ value: ApplicationLandingRoute; label: string }> = [
		{ value: '/dashboard', label: 'Tableau de bord' },
		{ value: '/scis', label: 'Portefeuille' },
		{ value: '/exploitation', label: 'Exploitation' },
		{ value: '/finance', label: 'Finance' },
		{ value: '/settings', label: "Paramètres de l'application" }
	];

	const notificationTypeLabels: Record<string, string> = {
		late_payment: 'Loyer en retard',
		bail_expiring: 'Bail expirant',
		quittance_pending: 'Quittance en attente',
		pno_expiring: 'PNO expirant',
		new_loyer: 'Nouveau loyer',
		new_associe: 'Nouvel associé',
		subscription_expiring: 'Abonnement expirant'
	};

	let preferences: ApplicationPreferences = $state({ ...DEFAULT_APPLICATION_PREFERENCES });
	let subscription: SubscriptionEntitlements | null = $state(null);
	let subscriptionError = $state('');

	let notifPreferences: NotificationPreference[] = $state([]);
	let notifLoading = $state(true);
	let notifSaving = $state(false);
	let notifError = $state('');

	let landingRouteLabel = $derived(
		landingRouteOptions.find((option) => option.value === preferences.defaultLandingRoute)?.label ??
		'Tableau de bord'
	);
	let densityLabel = $derived(preferences.density === 'compact' ? 'Compacte' : 'Confortable');

	onMount(() => {
		preferences = readApplicationPreferences();

		Promise.allSettled([fetchSubscriptionEntitlements(), fetchNotificationPreferences()])
			.then(([subResult, notifResult]) => {
				if (subResult.status === 'fulfilled') {
					subscription = subResult.value;
				} else {
					subscriptionError = formatApiErrorMessage(
						subResult.reason,
						"Impossible de charger l'offre active."
					);
				}

				if (notifResult.status === 'fulfilled') {
					notifPreferences = notifResult.value.preferences;
				} else {
					notifError = formatApiErrorMessage(
						notifResult.reason,
						'Impossible de charger les préférences de notification.'
					);
				}
			})
			.catch(() => {
				notifError = 'Impossible de charger les préférences de notification.';
			})
			.finally(() => {
				notifLoading = false;
			});
	});

	function handleSave() {
		saveApplicationPreferences(preferences);
		addToast({
			title: 'Paramètres enregistrés',
			description: "Les préférences d'application ont été mises à jour sur ce navigateur.",
			variant: 'success'
		});
	}

	async function handleNotifSave() {
		notifSaving = true;
		notifError = '';
		try {
			const result = await updateNotificationPreferences(notifPreferences);
			notifPreferences = result.preferences;
			addToast({
				title: 'Notifications mises a jour',
				description: 'Vos préférences de notification ont été enregistrées.',
				variant: 'success'
			});
		} catch (error) {
			notifError = formatApiErrorMessage(
				error,
				'Impossible de sauvegarder les préférences de notification.'
			);
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

<svelte:head><title>Paramètres | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<WorkspaceHeader
		eyebrow="Paramètres d'affichage"
		title="Preferences de l'application"
		subtitle="Les parametres ajustent uniquement l'experience locale du navigateur: point d'entree, densite, PDF et signaux. L'identite et l'offre restent dans Compte."
		contextLabel="Configuration active"
		contextValue={`${landingRouteLabel} - ${densityLabel}`}
		contextDetail={preferences.showPdfPreview ? 'Previsualisation PDF active.' : 'Previsualisation PDF desactivee.'}
	>
		<Button href="/account">Ouvrir le compte</Button>
		<Button href="/dashboard" variant="outline">Retour au tableau de bord</Button>
	</WorkspaceHeader>

	<WorkspaceActionBar
		eyebrow="Cadre des preferences"
		title="Reglages locaux, pas decisions metier"
		description="On ajuste ici la façon dont l'interface s'ouvre et se lit sur ce navigateur. Les parametres ne doivent pas concurrencer les ecrans metier."
	>
		<div class="sci-action-grid">
			<div class="sci-action-card">
				<p class="sci-action-card-title">Point d'entree</p>
				<p class="sci-action-card-value">{landingRouteLabel}</p>
				<p class="sci-action-card-body">Page ouverte apres connexion sur ce navigateur.</p>
			</div>
			<div class="sci-action-card">
				<p class="sci-action-card-title">Densite</p>
				<p class="sci-action-card-value">{densityLabel}</p>
				<p class="sci-action-card-body">Reglage de lecture applique a l'ensemble du shell connecte.</p>
			</div>
			<div class="sci-action-card">
				<p class="sci-action-card-title">Signaux</p>
				<p class="sci-action-card-value">{preferences.riskAlertsEnabled ? 'Alertes actives' : 'Alertes neutres'}</p>
				<p class="sci-action-card-body">Met en avant ou non les retards et risques dans les vues cles.</p>
			</div>
		</div>
		<div class="mt-5 sci-primary-actions">
			<Button onclick={handleSave}>Enregistrer les parametres</Button>
			<Button href="/account" variant="outline">Revenir au compte</Button>
		</div>
		{#snippet aside()}
			<WorkspaceRailCard
				title="Lecture immediate"
				description="Le panneau de droite rappelle les reglages actifs et l'impact de l'offre sans melanger les actions du compte."
			>
				<div class="space-y-3">
					<div class="sci-action-card">
						<p class="sci-action-card-title">PDF</p>
						<p class="sci-action-card-value">{preferences.showPdfPreview ? 'Preview active' : 'Download prioritaire'}</p>
					</div>
					{#if subscription}
						<div class="sci-action-card">
							<p class="sci-action-card-title">Capacite active</p>
							<p class="sci-action-card-value">{subscription.plan_name}</p>
							<p class="sci-action-card-body">
								{subscription.max_scis == null ? 'SCI illimitees' : `${subscription.remaining_scis ?? 0} SCI restantes`}
								-
								{subscription.max_biens == null ? 'Biens illimites' : `${subscription.remaining_biens ?? 0} biens restants`}
							</p>
						</div>
					{/if}
				</div>
			</WorkspaceRailCard>
		{/snippet}
	</WorkspaceActionBar>

	<div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
		<div class="space-y-6">
			<Card class="sci-section-card">
				<CardHeader>
					<div>
						<CardTitle class="text-lg">Preferences d'experience</CardTitle>
						<CardDescription>Ces reglages sont propres au navigateur courant et s'appliquent a tout l'espace connecte.</CardDescription>
					</div>
				</CardHeader>
				<CardContent class="space-y-6 pt-0">
					<label class="sci-field" for="settings-landing-route">
						<span class="sci-field-label">Page d'ouverture par defaut</span>
						<select
							id="settings-landing-route"
							name="settings-landing-route"
							class="sci-select"
							bind:value={preferences.defaultLandingRoute}
						>
							{#each landingRouteOptions as option (option.value)}
								<option value={option.value}>{option.label}</option>
							{/each}
						</select>
					</label>

					<label class="sci-field" for="settings-density">
						<span class="sci-field-label">Densite d'affichage</span>
						<select id="settings-density" name="settings-density" class="sci-select" bind:value={preferences.density}>
							<option value="comfortable">Confortable</option>
							<option value="compact">Compacte</option>
						</select>
					</label>

					<div class="grid gap-3 md:grid-cols-3">
						<label class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="font-semibold text-slate-900 dark:text-slate-100">Previsualisation PDF</p>
									<p class="mt-1 text-slate-500 dark:text-slate-400">Affiche les quittances directement dans l'interface.</p>
								</div>
								<input type="checkbox" bind:checked={preferences.showPdfPreview} aria-label="Activer la previsualisation PDF" />
							</div>
						</label>

						<label class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="font-semibold text-slate-900 dark:text-slate-100">Digest email</p>
									<p class="mt-1 text-slate-500 dark:text-slate-400">Preference de reception des rappels et syntheses.</p>
								</div>
								<input type="checkbox" bind:checked={preferences.emailDigestEnabled} aria-label="Activer le digest email" />
							</div>
						</label>

						<label class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="font-semibold text-slate-900 dark:text-slate-100">Alertes de risque</p>
									<p class="mt-1 text-slate-500 dark:text-slate-400">Priorise les retards et charges anormales dans les vues cles.</p>
								</div>
								<input type="checkbox" bind:checked={preferences.riskAlertsEnabled} aria-label="Activer les alertes de risque" />
							</div>
						</label>
					</div>
				</CardContent>
			</Card>

			<!-- Notification Preferences Section -->
			<Card class="sci-section-card">
				<CardHeader>
					<div>
						<CardTitle class="text-lg">Notifications</CardTitle>
						<CardDescription>Configurez les types de notifications que vous souhaitez recevoir par email et dans l'application.</CardDescription>
					</div>
				</CardHeader>
				<CardContent class="space-y-4 pt-0">
					{#if notifLoading}
						<div class="flex items-center justify-center py-8">
							<div class="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900 dark:border-slate-600 dark:border-t-slate-100"></div>
							<span class="ml-3 text-sm text-slate-500 dark:text-slate-400">Chargement des preferences...</span>
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
							<Button onclick={handleNotifSave} disabled={notifSaving}>
								{notifSaving ? 'Enregistrement...' : 'Enregistrer les notifications'}
							</Button>
						</div>
					{/if}
				</CardContent>
			</Card>
		</div>

		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Impact des reglages</CardTitle>
					<CardDescription>Lecture immediate de la configuration active sur ce navigateur, sans melanger cela avec les actions de compte.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="grid gap-3 pt-0">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Point d'entree</p>
					<p class="mt-2 text-base font-semibold text-slate-900 dark:text-slate-100">{landingRouteLabel}</p>
					<p class="mt-1 text-slate-500 dark:text-slate-400">La premiere page ouverte apres connexion sur ce navigateur.</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Densite d'affichage</p>
					<p class="mt-2 text-base font-semibold text-slate-900 dark:text-slate-100">{densityLabel}</p>
					<p class="mt-1 text-slate-500 dark:text-slate-400">
						{preferences.density === 'compact'
							? "Priorise la densite d'information pour une consultation rapide."
							: "Laisse davantage d'air entre les blocs pour une lecture confortable."}
					</p>
				</div>
				<div class="grid gap-3 md:grid-cols-2">
					<div class="rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-950">
						<p class="font-semibold text-slate-900 dark:text-slate-100">PDF</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							{preferences.showPdfPreview ? 'Previsualisation integree active.' : 'Telechargement sans preview priorise.'}
						</p>
					</div>
					<div class="rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-950">
						<p class="font-semibold text-slate-900 dark:text-slate-100">Alertes</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							{preferences.riskAlertsEnabled ? 'Les signaux de risque sont mis en avant.' : 'Les vues restent neutres sans priorisation des risques.'}
						</p>
					</div>
				</div>
				{#if !notifLoading && notifPreferences.length > 0}
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
						<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Notifications</p>
						<p class="mt-2 text-base font-semibold text-slate-900 dark:text-slate-100">
							{notifPreferences.filter((p) => p.email_enabled).length}/{notifPreferences.length} email
							-
							{notifPreferences.filter((p) => p.in_app_enabled).length}/{notifPreferences.length} in-app
						</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">Canaux actifs par type de notification.</p>
					</div>
				{/if}
				{#if subscription}
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
						<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Capacite active</p>
						<p class="mt-2 text-base font-semibold text-slate-900 dark:text-slate-100">{subscription.plan_name}</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							{subscription.max_scis == null ? 'SCI illimitees' : `${subscription.remaining_scis ?? 0} SCI restantes`}
							-
							{subscription.max_biens == null ? 'Biens illimites' : `${subscription.remaining_biens ?? 0} biens restants`}
						</p>
					</div>
				{:else if subscriptionError}
					<p class="sci-inline-alert sci-inline-alert-error">{subscriptionError}</p>
				{/if}
				<div class="grid gap-2 border-t border-slate-200 pt-3 dark:border-slate-800">
					<Button href="/account" variant="outline" class="justify-start">Aller au compte</Button>
					<Button href="/account/privacy" variant="outline" class="justify-start">Ouvrir la confidentialite</Button>
				</div>
			</CardContent>
		</Card>
	</div>
</section>
