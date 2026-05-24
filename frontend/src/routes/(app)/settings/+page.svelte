<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import type { User } from '@supabase/supabase-js';
	import {
		fetchSubscriptionEntitlements,
		fetchNotificationPreferences,
		type SubscriptionEntitlements,
		type NotificationPreference
	} from '$lib/api';
	import {
		DEFAULT_APPLICATION_PREFERENCES,
		readApplicationPreferences,
		type ApplicationPreferences
	} from '$lib/settings/application-preferences';
	import { theme, type ThemePreference } from '$lib/stores/theme';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { User as UserIcon, CreditCard, Bell, Shield, Settings } from 'lucide-svelte';

	// Subcomponents
	import SettingsProfil from './components/SettingsProfil.svelte';
	import SettingsAbonnement from './components/SettingsAbonnement.svelte';
	import SettingsNotifications from './components/SettingsNotifications.svelte';
	import SettingsConfidentialite from './components/SettingsConfidentialite.svelte';
	import SettingsPreferences from './components/SettingsPreferences.svelte';

	const subscriptionCtx = getContext<SubscriptionEntitlements>('subscription');
	const isDemo = !subscriptionCtx?.is_active;

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

	// Contexts
	const user = getContext<User>('user');
	const email = user?.email || 'Compte non connecté';

	// Subscription & Notifications States (shared/fetched on parent)
	let subscription = $state<SubscriptionEntitlements | null>(null);
	let subscriptionLoading = $state(true);
	let subscriptionError = $state('');

	let notifPreferences = $state<NotificationPreference[]>([]);
	let notifLoading = $state(true);
	let notifError = $state('');

	// Display Preferences States
	let preferences: ApplicationPreferences = $state({ ...DEFAULT_APPLICATION_PREFERENCES });
	let currentTheme: ThemePreference = $state('system');

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
			Gerez votre profil, votre abonnement, vos notifications et vos donnees personnelles.
		</p>
	</header>

	<!-- Tab bar -->
	<nav
		class="mt-4 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm dark:border-slate-800 dark:bg-slate-950"
		aria-label="Sections des parametres"
	>
		<div class="flex gap-2 overflow-x-auto" role="tablist" aria-label="Navigation parametres">
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
			<SettingsProfil {user} {email} />
		{:else if activeTab === 'abonnement'}
			<SettingsAbonnement
				bind:subscription
				{subscriptionLoading}
				{subscriptionError}
			/>
		{:else if activeTab === 'notifications'}
			<SettingsNotifications
				bind:notifPreferences
				{notifLoading}
				{notifError}
				{isDemo}
			/>
		{:else if activeTab === 'confidentialite'}
			<SettingsConfidentialite />
		{:else if activeTab === 'preferences'}
			<SettingsPreferences
				bind:preferences
				bind:currentTheme
			/>
		{/if}
	</div>
</section>
