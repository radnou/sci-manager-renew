<script lang="ts">
	import { onMount } from 'svelte';
	import { getContext } from 'svelte';
	import { goto } from '$app/navigation';
	import type { User } from '@supabase/supabase-js';
	import {
		fetchSubscriptionEntitlements,
		fetchNotificationPreferences,
		updateNotificationPreferences,
		cancelSubscription,
		API_URL,
		type SubscriptionEntitlements,
		type NotificationPreference
	} from '$lib/api';
	import { getCurrentSession } from '$lib/auth/session';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { addToast } from '$lib/components/ui/toast';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import {
		DEFAULT_APPLICATION_PREFERENCES,
		readApplicationPreferences,
		saveApplicationPreferences,
		type ApplicationLandingRoute,
		type ApplicationPreferences
	} from '$lib/settings/application-preferences';
	import { theme, type ThemePreference } from '$lib/stores/theme';
	import { User as UserIcon, CreditCard, Bell, Shield, Settings, ExternalLink, AlertTriangle } from 'lucide-svelte';
	import ConfirmDeleteModal from '$lib/components/ConfirmDeleteModal.svelte';

	// --- Tab management ---
	type TabId = 'profil' | 'abonnement' | 'notifications' | 'confidentialite' | 'preferences';

	const tabs: Array<{ id: TabId; label: string; icon: typeof UserIcon }> = [
		{ id: 'profil', label: 'Profil', icon: UserIcon },
		{ id: 'abonnement', label: 'Abonnement', icon: CreditCard },
		{ id: 'notifications', label: 'Notifications', icon: Bell },
		{ id: 'confidentialite', label: 'Confidentialité', icon: Shield },
		{ id: 'preferences', label: 'Préférences', icon: Settings }
	];

	let activeTab: TabId = $state('profil');

	function setTab(tab: TabId) {
		activeTab = tab;
		window.history.replaceState(null, '', `#${tab}`);
	}

	// --- Profile tab ---
	const user = getContext<User>('user');
	const email = user?.email || 'Compte non connecté';

	let newPassword = $state('');
	let newPasswordConfirm = $state('');
	let passwordLoading = $state(false);
	let passwordError = $state('');
	let passwordSuccess = $state(false);
	const passwordMinLength = 8;

	async function handlePasswordChange() {
		passwordError = '';
		passwordSuccess = false;

		if (newPassword !== newPasswordConfirm) {
			passwordError = 'Les mots de passe ne correspondent pas.';
			return;
		}

		if (newPassword.length < passwordMinLength) {
			passwordError = `Le mot de passe doit contenir au moins ${passwordMinLength} caractères.`;
			return;
		}

		passwordLoading = true;

		const { error } = await supabase.auth.updateUser({ password: newPassword });

		if (error) {
			passwordError = 'Erreur lors de la mise à jour du mot de passe.';
		} else {
			passwordSuccess = true;
			newPassword = '';
			newPasswordConfirm = '';
			addToast({
				title: 'Mot de passe mis à jour',
				description: 'Votre mot de passe a été modifié avec succès.',
				variant: 'success'
			});
		}

		passwordLoading = false;
	}

	// --- App preferences (Profil tab) ---
	const landingRouteOptions: Array<{ value: ApplicationLandingRoute; label: string }> = [
		{ value: '/dashboard', label: 'Tableau de bord' },
		{ value: '/scis', label: 'Portefeuille' },
		{ value: '/exploitation', label: 'Exploitation' },
		{ value: '/finances', label: 'Finances' },
		{ value: '/settings', label: "Paramètres" }
	];

	let preferences: ApplicationPreferences = $state({ ...DEFAULT_APPLICATION_PREFERENCES });
	let currentTheme: ThemePreference = $state('system');

	function handleSavePreferences() {
		saveApplicationPreferences(preferences);
		addToast({
			title: 'Paramètres enregistrés',
			description: "Les préférences ont été mises à jour sur ce navigateur.",
			variant: 'success'
		});
	}

	// --- Subscription tab ---
	let subscription: SubscriptionEntitlements | null = $state(null);
	let subscriptionLoading = $state(true);
	let subscriptionError = $state('');
	let cancelStep = $state(0);
	let cancelError = $state('');
	let portalLoading = $state(false);

	function getCapacityLabel(sub: SubscriptionEntitlements): string {
		if (sub.max_scis == null) return 'SCI et biens illimités';
		return `${sub.current_scis}/${sub.max_scis} SCI · ${sub.current_biens}/${sub.max_biens} biens`;
	}

	async function openCustomerPortal() {
		portalLoading = true;
		try {
			const { apiFetch } = await import('$lib/api');
			const data: { url: string } = await apiFetch('/api/v1/stripe/customer-portal', {
				method: 'POST'
			});
			window.location.href = data.url;
		} catch {
			addToast({
				title: 'Erreur',
				description: "Impossible d'ouvrir le portail de gestion d'abonnement.",
				variant: 'error'
			});
			portalLoading = false;
		}
	}

	async function handleCancel() {
		if (cancelStep === 0) {
			cancelStep = 1;
			return;
		}
		if (cancelStep === 1) {
			cancelStep = 2;
			try {
				const result = await cancelSubscription();
				addToast({ title: result.message, variant: 'success' });
				cancelStep = 0;
				subscription = await fetchSubscriptionEntitlements();
			} catch (err) {
				cancelError = formatApiErrorMessage(err, 'Erreur lors de la résiliation.');
				cancelStep = 1;
			}
		}
	}

	// --- Notifications tab ---
	const notificationTypeLabels: Record<string, string> = {
		late_payment: 'Loyer en retard',
		bail_expiring: 'Bail expirant',
		quittance_pending: 'Quittance en attente',
		pno_expiring: 'PNO expirant',
		new_loyer: 'Nouveau loyer',
		new_associe: 'Nouvel associé',
		subscription_expiring: 'Abonnement expirant'
	};

	let notifPreferences: NotificationPreference[] = $state([]);
	let notifLoading = $state(true);
	let notifSaving = $state(false);
	let notifError = $state('');

	async function handleNotifSave() {
		notifSaving = true;
		notifError = '';
		try {
			const result = await updateNotificationPreferences(notifPreferences);
			notifPreferences = result.preferences;
			addToast({
				title: 'Notifications mises à jour',
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

	// --- Privacy tab ---
	interface DataSummary {
		user_id: string;
		email: string;
		created_at: string;
		data_summary: {
			sci_count: number;
			biens_count: number;
			loyers_count: number;
			associes_count: number;
			account_created: string;
			last_sign_in: string;
		};
	}

	let privacyLoading = $state(false);
	let exportLoading = $state(false);
	let deleteLoading = $state(false);
	let dataSummary = $state<DataSummary | null>(null);
	let showDeleteConfirm = $state(false);
	let deleteConfirmEmail = $state('');
	let privacyLoadError = $state('');

	async function getAccessToken(): Promise<string | null> {
		const session = await getCurrentSession();
		if (!session?.access_token) {
			goto('/login');
			return null;
		}
		return session.access_token;
	}

	async function loadDataSummary() {
		privacyLoading = true;
		privacyLoadError = '';
		try {
			const token = await getAccessToken();
			if (!token) return;

			const response = await fetch(`${API_URL}/api/v1/gdpr/data-summary`, {
				headers: { Authorization: `Bearer ${token}` }
			});

			if (response.ok) {
				dataSummary = await response.json();
			} else {
				privacyLoadError = 'Impossible de charger le résumé des données personnelles.';
			}
		} catch {
			privacyLoadError = 'Erreur réseau pendant le chargement des données personnelles.';
		} finally {
			privacyLoading = false;
		}
	}

	async function exportData() {
		exportLoading = true;
		try {
			const token = await getAccessToken();
			if (!token) return;

			const response = await fetch(`${API_URL}/api/v1/gdpr/data-export`, {
				headers: { Authorization: `Bearer ${token}` }
			});

			if (response.ok) {
				const data = (await response.json()) as { export_url?: string; expires_at?: string };
				if (data.export_url) {
					window.open(data.export_url, '_blank', 'noopener,noreferrer');
					addToast({
						title: 'Export prêt. Le téléchargement a été ouvert dans un nouvel onglet.',
						variant: 'success'
					});
				} else {
					addToast({
						title: "Export créé, mais aucun lien de téléchargement n'a été retourné.",
						variant: 'error'
					});
				}
			} else {
				addToast({ title: "Erreur lors de l'export des données", variant: 'error' });
			}
		} catch {
			addToast({ title: 'Erreur réseau', variant: 'error' });
		} finally {
			exportLoading = false;
		}
	}

	function isDeleteConfirmValid(): boolean {
		if (!dataSummary?.email) return false;
		return deleteConfirmEmail.trim().toLowerCase() === dataSummary.email.trim().toLowerCase();
	}

	async function deleteAccount() {
		deleteLoading = true;
		try {
			const token = await getAccessToken();
			if (!token) return;

			const response = await fetch(`${API_URL}/api/v1/gdpr/account`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});

			if (response.ok) {
				addToast({
					title: 'Compte supprimé avec succès. Redirection...',
					variant: 'success'
				});
				await supabase.auth.signOut();
				setTimeout(() => goto('/'), 2000);
			} else {
				addToast({ title: 'Erreur lors de la suppression du compte', variant: 'error' });
			}
		} catch {
			addToast({ title: 'Erreur réseau', variant: 'error' });
		} finally {
			deleteLoading = false;
			showDeleteConfirm = false;
		}
	}

	function formatDate(dateStr: string | null | undefined): string {
		if (!dateStr || dateStr === 'None') return 'Non disponible';
		try {
			return new Date(dateStr).toLocaleDateString('fr-FR', {
				day: 'numeric',
				month: 'long',
				year: 'numeric'
			});
		} catch {
			return 'Non disponible';
		}
	}

	function formatDateTime(dateStr: string | null | undefined): string {
		if (!dateStr || dateStr === 'None') return 'Non disponible';
		try {
			return new Date(dateStr).toLocaleDateString('fr-FR', {
				day: 'numeric',
				month: 'long',
				year: 'numeric',
				hour: '2-digit',
				minute: '2-digit'
			});
		} catch {
			return 'Non disponible';
		}
	}

	// --- Lifecycle ---
	onMount(() => {
		// Read hash for initial tab
		const hash = window.location.hash.replace('#', '') as TabId;
		if (tabs.some((t) => t.id === hash)) {
			activeTab = hash;
		}

		// Listen for hash changes
		function onHashChange() {
			const h = window.location.hash.replace('#', '') as TabId;
			if (tabs.some((t) => t.id === h)) {
				activeTab = h;
			}
		}
		window.addEventListener('hashchange', onHashChange);

		// Load preferences
		preferences = readApplicationPreferences();
		const unsubscribeTheme = theme.subscribe((value) => {
			currentTheme = value;
		});

		// Load subscription + notification preferences
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
				subscriptionLoading = false;
				notifLoading = false;
			});

		// Load GDPR data summary
		loadDataSummary();

		return () => {
			unsubscribeTheme();
			window.removeEventListener('hashchange', onHashChange);
		};
	});
</script>

<svelte:head><title>Paramètres | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	<!-- Page header -->
	<header class="sci-page-header">
		<p class="sci-eyebrow">Mon compte</p>
		<h1 class="sci-page-title">Paramètres</h1>
		<p class="sci-page-subtitle">
			Gérez votre profil, votre abonnement, vos notifications et vos données personnelles.
		</p>
	</header>

	<!-- Tab bar -->
	<nav
		class="mt-4 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm dark:border-slate-800 dark:bg-slate-950"
		aria-label="Sections des paramètres"
	>
		<div class="flex gap-2 overflow-x-auto" role="tablist" aria-label="Navigation paramètres">
			{#each tabs as tab (tab.id)}
				<button
					type="button"
					onclick={() => setTab(tab.id)}
					role="tab"
					aria-selected={activeTab === tab.id}
					aria-controls={`panel-${tab.id}`}
					id={`tab-${tab.id}`}
					class="relative flex items-center gap-1.5 whitespace-nowrap rounded-xl px-3.5 py-2.5 text-sm font-medium transition-colors {activeTab === tab.id
						? 'bg-sky-600 text-white shadow-sm'
						: 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'}"
				>
					<tab.icon class="h-4 w-4" aria-hidden="true" />
					{tab.label}
				</button>
			{/each}
		</div>
	</nav>

	<!-- Tab panels -->
	<div class="mt-6">
		{#if activeTab === 'profil'}
			<div id="panel-profil" role="tabpanel" aria-labelledby="tab-profil" class="space-y-6">
				<!-- Identity -->
				<Card class="sci-section-card">
					<CardHeader>
						<div>
							<CardTitle class="text-lg">Identité</CardTitle>
							<CardDescription>Adresse email de connexion et mode d'accès.</CardDescription>
						</div>
					</CardHeader>
					<CardContent class="grid gap-4 pt-0 sm:grid-cols-2">
						<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
							<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Email</p>
							<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{email}</p>
						</div>
						<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
							<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Mode d'accès</p>
							<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
								{user?.email ? 'Connexion par lien sécurisé' : 'Aucune session active'}
							</p>
						</div>
					</CardContent>
				</Card>

				<!-- Password change -->
				<Card class="sci-section-card">
					<CardHeader>
						<div>
							<CardTitle class="text-lg">Sécurité</CardTitle>
							<CardDescription>Modifiez votre mot de passe pour sécuriser votre compte.</CardDescription>
						</div>
					</CardHeader>
					<CardContent class="pt-0">
						<form class="max-w-md space-y-4" onsubmit={(e) => { e.preventDefault(); handlePasswordChange(); }}>
							<label class="sci-field">
								<span class="sci-field-label">Nouveau mot de passe</span>
								<Input
									type="password"
									bind:value={newPassword}
									placeholder="••••••••"
									disabled={passwordLoading}
									autocomplete="new-password"
								/>
							</label>
							<label class="sci-field">
								<span class="sci-field-label">Confirmer le nouveau mot de passe</span>
								<Input
									type="password"
									bind:value={newPasswordConfirm}
									placeholder="••••••••"
									disabled={passwordLoading}
									autocomplete="new-password"
								/>
							</label>

							{#if passwordError}
								<p class="sci-inline-alert sci-inline-alert-error">{passwordError}</p>
							{/if}

							{#if passwordSuccess}
								<p class="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
									Mot de passe mis à jour avec succès.
								</p>
							{/if}

							<Button
								type="submit"
								disabled={passwordLoading || !newPassword || !newPasswordConfirm || newPassword !== newPasswordConfirm || newPassword.length < passwordMinLength}
							>
								{passwordLoading ? 'Mise à jour...' : 'Modifier le mot de passe'}
							</Button>
						</form>
					</CardContent>
				</Card>

				</div>

		{:else if activeTab === 'abonnement'}
			<div id="panel-abonnement" role="tabpanel" aria-labelledby="tab-abonnement">
				{#if subscriptionLoading}
					<div class="sci-loading" role="status" aria-label="Chargement"></div>
				{:else if subscriptionError}
					<div class="sci-inline-alert sci-inline-alert-error" role="alert">{subscriptionError}</div>
				{:else if subscription}
					<div class="grid gap-6 lg:grid-cols-2">
						<Card class="sci-section-card">
							<CardHeader>
								<div class="flex items-center gap-3">
									<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-100 dark:bg-sky-900/30">
										<CreditCard class="h-5 w-5 text-sky-600 dark:text-sky-400" />
									</div>
									<div>
										<CardTitle class="text-lg">Offre active</CardTitle>
										<CardDescription>Votre plan et ses limites</CardDescription>
									</div>
								</div>
							</CardHeader>
							<CardContent class="grid gap-4 pt-0">
								<div class="rounded-2xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900">
									<p class="sci-eyebrow">Plan actuel</p>
									<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
										{subscription.plan_name}
									</p>
									<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{getCapacityLabel(subscription)}</p>
								</div>

								<div class="grid gap-3 sm:grid-cols-2">
									<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
										<p class="sci-eyebrow">SCI</p>
										<p class="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
											{subscription.current_scis}{#if subscription.max_scis != null}<span class="text-sm font-normal text-slate-400"> / {subscription.max_scis}</span>{/if}
										</p>
									</div>
									<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
										<p class="sci-eyebrow">Biens</p>
										<p class="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
											{subscription.current_biens}{#if subscription.max_biens != null}<span class="text-sm font-normal text-slate-400"> / {subscription.max_biens}</span>{/if}
										</p>
									</div>
								</div>
							</CardContent>
						</Card>

						<Card class="sci-section-card">
							<CardHeader>
								<div>
									<CardTitle class="text-lg">Actions</CardTitle>
									<CardDescription>Gérez votre abonnement et votre facturation</CardDescription>
								</div>
							</CardHeader>
							<CardContent class="grid gap-3 pt-0">
								<Button href="/pricing" class="justify-start gap-2">
									<ExternalLink class="h-4 w-4" aria-hidden="true" />
									Changer d'offre
								</Button>

								{#if subscription.plan_key !== 'free'}
									<Button
										variant="outline"
										class="justify-start gap-2"
										onclick={openCustomerPortal}
										disabled={portalLoading}
									>
										<CreditCard class="h-4 w-4" aria-hidden="true" />
										{portalLoading ? 'Ouverture...' : 'Gérer la facturation (Stripe)'}
									</Button>
								{/if}

								<!-- Résiliation en 3 clics (loi 16 août 2022) -->
								{#if subscription.is_active && subscription.status !== 'no_subscription'}
									<hr class="my-2 border-slate-200 dark:border-slate-700" />

									{#if cancelStep === 0}
										<Button
											variant="outline"
											class="justify-start gap-2 text-rose-600 hover:bg-rose-50 hover:text-rose-700 dark:text-rose-400 dark:hover:bg-rose-950"
											onclick={handleCancel}
										>
											<AlertTriangle class="h-4 w-4" aria-hidden="true" />
											Résilier mon abonnement
										</Button>
									{:else if cancelStep === 1}
										<div class="rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-800 dark:bg-rose-950/30">
											<p class="text-sm font-medium text-rose-800 dark:text-rose-200">
												Confirmez la résiliation
											</p>
											<p class="mt-1 text-xs text-rose-600 dark:text-rose-400">
												Votre abonnement restera actif jusqu'à la fin de la période en cours.
												Vous conserverez l'accès à toutes les fonctionnalités jusqu'à cette date.
											</p>
											{#if cancelError}
												<p class="mt-2 text-xs font-medium text-rose-700" role="alert">{cancelError}</p>
											{/if}
											<div class="mt-3 flex gap-2">
												<Button variant="destructive" size="sm" onclick={handleCancel}>
													Confirmer la résiliation
												</Button>
												<Button variant="outline" size="sm" onclick={() => { cancelStep = 0; cancelError = ''; }}>
													Annuler
												</Button>
											</div>
										</div>
									{:else}
										<div class="flex items-center gap-2 text-sm text-slate-500">
											<div class="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-rose-500"></div>
											Résiliation en cours...
										</div>
									{/if}
								{/if}
							</CardContent>
						</Card>
					</div>
				{:else}
					<div class="sci-empty-state">
						<p>Aucun abonnement actif. Choisissez un plan pour accéder à GérerSCI.</p>
						<Button href="/pricing" class="mt-4">Choisir un plan</Button>
					</div>
				{/if}
			</div>

		{:else if activeTab === 'notifications'}
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
								<Button onclick={handleNotifSave} disabled={notifSaving}>
									{notifSaving ? 'Enregistrement...' : 'Enregistrer les notifications'}
								</Button>
							</div>
						{/if}
					</CardContent>
				</Card>
			</div>

		{:else if activeTab === 'confidentialite'}
			<div id="panel-confidentialite" role="tabpanel" aria-labelledby="tab-confidentialite" class="space-y-6">
				{#if privacyLoading}
					<div class="sci-loading" role="status" aria-label="Chargement"></div>
				{:else if !dataSummary}
					<Card class="sci-section-card">
						<CardContent class="py-8">
							<p class="sci-inline-alert sci-inline-alert-error">
								{privacyLoadError || "Impossible de charger les données personnelles. Rechargez la page."}
							</p>
						</CardContent>
					</Card>
				{:else}
					<!-- Data summary -->
					<Card class="sci-section-card">
						<CardHeader>
							<div>
								<CardTitle class="text-lg">Résumé des données</CardTitle>
								<CardDescription>Vue d'ensemble des informations stockées sur le compte connecté.</CardDescription>
							</div>
						</CardHeader>
						<CardContent class="grid gap-4 pt-0 md:grid-cols-2">
							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Email</p>
								<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{dataSummary.email}</p>
							</div>
							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Compte créé le</p>
								<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{formatDate(dataSummary.created_at)}</p>
							</div>
							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Dernière connexion</p>
								<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{formatDateTime(dataSummary.data_summary.last_sign_in)}</p>
							</div>
							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Données stockées</p>
								<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
									{dataSummary.data_summary.sci_count} SCI ·
									{dataSummary.data_summary.biens_count} biens ·
									{dataSummary.data_summary.loyers_count} loyers ·
									{dataSummary.data_summary.associes_count} associés
								</p>
							</div>
						</CardContent>
					</Card>

					<!-- Export -->
					<Card class="sci-section-card">
						<CardHeader>
							<div>
								<CardTitle class="text-lg">Export des données (JSON)</CardTitle>
								<CardDescription>Droit à la portabilité (RGPD Art. 20). Téléchargez une copie complète de vos données.</CardDescription>
							</div>
						</CardHeader>
						<CardContent class="space-y-4 pt-0">
							<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
								<p class="text-sm text-slate-700 dark:text-slate-300">
									L'export contient toutes les données rattachées au compte dans un fichier JSON structuré :
								</p>
								<ul class="mt-2 list-inside list-disc space-y-1 text-sm text-slate-600 dark:text-slate-400">
									<li>Informations du compte (email, dates de création et connexion)</li>
									<li>SCI et associés</li>
									<li>Biens immobiliers</li>
									<li>Loyers enregistrés</li>
									<li>Charges et données fiscales</li>
								</ul>
								<p class="mt-3 text-xs text-slate-500 dark:text-slate-500">
									Le lien de téléchargement est valide 30 minutes. L'export est limité à 3 demandes par heure.
								</p>
							</div>

							<Button onclick={exportData} disabled={exportLoading} class="w-full sm:w-auto">
								{#if exportLoading}
									<span class="flex items-center gap-2">
										<svg class="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
											<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
											<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
										</svg>
										Export en cours...
									</span>
								{:else}
									Télécharger mes données (JSON)
								{/if}
							</Button>
						</CardContent>
					</Card>

					<!-- Delete account -->
					<Card class="sci-section-card border-red-200 dark:border-red-900">
						<CardHeader>
							<div>
								<CardTitle class="text-red-600 dark:text-red-400">Suppression du compte</CardTitle>
								<CardDescription>Droit à l'effacement (RGPD Art. 17). Cette action est définitive et irréversible.</CardDescription>
							</div>
						</CardHeader>
						<CardContent class="space-y-4 pt-0">
							<div class="rounded-2xl bg-red-50 p-4 dark:bg-red-900/20">
								<p class="mb-2 text-sm font-semibold text-red-800 dark:text-red-300">
									Attention : action irréversible
								</p>
								<p class="text-sm text-red-700 dark:text-red-400">
									La suppression du compte entraîne l'effacement définitif de :
								</p>
								<ul class="mt-2 list-inside list-disc space-y-1 text-sm text-red-700 dark:text-red-400">
									<li>Toutes les SCI ({dataSummary.data_summary.sci_count}) et leurs associés ({dataSummary.data_summary.associes_count})</li>
									<li>Tous les biens immobiliers ({dataSummary.data_summary.biens_count})</li>
									<li>Tous les loyers ({dataSummary.data_summary.loyers_count}), charges et données fiscales</li>
									<li>Tous les documents uploadés</li>
								</ul>
								<p class="mt-3 text-xs text-red-600 dark:text-red-500">
									Les données de facturation Stripe sont anonymisées (non supprimées) pour respecter les obligations légales de conservation de 10 ans (Code Général des Impôts).
								</p>
							</div>

							<Button variant="destructive" onclick={() => (showDeleteConfirm = true)}>
								Supprimer définitivement mon compte
							</Button>

							<ConfirmDeleteModal
								open={showDeleteConfirm}
								entityName={dataSummary.email}
								entityType="votre compte"
								warningMessage="La suppression du compte entraîne l'effacement définitif de toutes vos SCI ({dataSummary.data_summary.sci_count}), biens ({dataSummary.data_summary.biens_count}), loyers ({dataSummary.data_summary.loyers_count}), associés ({dataSummary.data_summary.associes_count}) et documents. Les données de facturation Stripe sont anonymisées. Cette action est irréversible."
								loading={deleteLoading}
								onConfirm={deleteAccount}
								onCancel={() => { showDeleteConfirm = false; deleteConfirmEmail = ''; }}
							/>
						</CardContent>
					</Card>

					<!-- RGPD contact -->
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
						<div class="flex flex-wrap gap-6">
							<div>
								<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Contact RGPD</p>
								<a href="mailto:privacy@gerersci.fr" class="mt-1 text-cyan-600 underline-offset-4 hover:underline dark:text-cyan-300">
									privacy@gerersci.fr
								</a>
							</div>
							<div>
								<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Autorité de contrôle</p>
								<a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer" class="mt-1 text-cyan-600 underline-offset-4 hover:underline dark:text-cyan-300">
									CNIL
								</a>
							</div>
						</div>
					</div>
				{/if}
			</div>

		{:else if activeTab === 'preferences'}
			<div id="panel-preferences" role="tabpanel" aria-labelledby="tab-preferences" class="space-y-6">
				<Card class="sci-section-card">
					<CardHeader>
						<div>
							<CardTitle class="text-lg">Préférences d'affichage</CardTitle>
							<CardDescription>Réglages propres au navigateur courant : page d'ouverture, densité, thème.</CardDescription>
						</div>
					</CardHeader>
					<CardContent class="space-y-6 pt-0">
						<label class="sci-field" for="settings-landing-route">
							<span class="sci-field-label">Page d'ouverture par défaut</span>
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
							<span class="sci-field-label">Densité d'affichage</span>
							<select id="settings-density" name="settings-density" class="sci-select" bind:value={preferences.density}>
								<option value="comfortable">Confortable</option>
								<option value="compact">Compacte</option>
							</select>
						</label>

						<label class="sci-field" for="settings-theme">
							<span class="sci-field-label">Thème</span>
							<select
								id="settings-theme"
								name="settings-theme"
								class="sci-select"
								bind:value={currentTheme}
								onchange={(event) => theme.set((event.currentTarget as HTMLSelectElement).value as ThemePreference)}
							>
								<option value="system">Système</option>
								<option value="light">Clair</option>
								<option value="dark">Sombre</option>
							</select>
						</label>

						<div class="grid gap-3 md:grid-cols-3">
							<label class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
								<div class="flex items-start justify-between gap-3">
									<div>
										<p class="font-semibold text-slate-900 dark:text-slate-100">Prévisualisation PDF</p>
										<p class="mt-1 text-slate-500 dark:text-slate-400">Affiche les quittances directement dans l'interface.</p>
									</div>
									<input type="checkbox" bind:checked={preferences.showPdfPreview} aria-label="Activer la prévisualisation PDF" />
								</div>
							</label>

							<label class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
								<div class="flex items-start justify-between gap-3">
									<div>
										<p class="font-semibold text-slate-900 dark:text-slate-100">Digest email</p>
										<p class="mt-1 text-slate-500 dark:text-slate-400">Préférence de réception des rappels et synthèses.</p>
									</div>
									<input type="checkbox" bind:checked={preferences.emailDigestEnabled} aria-label="Activer le digest email" />
								</div>
							</label>

							<label class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
								<div class="flex items-start justify-between gap-3">
									<div>
										<p class="font-semibold text-slate-900 dark:text-slate-100">Alertes de risque</p>
										<p class="mt-1 text-slate-500 dark:text-slate-400">Priorise les retards et charges anormales dans les vues clés.</p>
									</div>
									<input type="checkbox" bind:checked={preferences.riskAlertsEnabled} aria-label="Activer les alertes de risque" />
								</div>
							</label>
						</div>

						<Button onclick={handleSavePreferences}>Enregistrer les préférences</Button>
					</CardContent>
				</Card>
			</div>
		{/if}
	</div>
</section>
