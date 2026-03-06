<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchSubscriptionEntitlements, type SubscriptionEntitlements } from '$lib/api';
	import { getCurrentSession } from '$lib/auth/session';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { getStoredActiveSciId } from '$lib/portfolio/active-sci';
	import { readApplicationPreferences } from '$lib/settings/application-preferences';

	let email = 'Compte non connecté';
	let accessMode = 'Session sécurisée';
	let activeSciId = '';
	let defaultLandingRoute = '/dashboard';
	let subscription: SubscriptionEntitlements | null = null;
	let subscriptionError = '';

	$: activeSciStatus = activeSciId ? 'Une SCI active est mémorisée' : 'Aucune SCI active mémorisée';
	$: activeSciDetail = activeSciId ? 'Le cockpit reviendra sur la dernière société suivie.' : 'Sélectionne une SCI dans le portefeuille pour cadrer les vues métier.';

	onMount(async () => {
		const session = await getCurrentSession();
		email = session?.user?.email || 'Compte non connecté';
		accessMode = session?.user?.email ? 'Connexion par lien sécurisé' : 'Aucune session active';
		activeSciId = getStoredActiveSciId() || '';
		defaultLandingRoute = readApplicationPreferences().defaultLandingRoute;
		try {
			subscription = await fetchSubscriptionEntitlements();
		} catch (error) {
			subscriptionError = formatApiErrorMessage(
				error,
				"Impossible de charger l'offre active du compte."
			);
		}
	});
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Compte • Gouvernance utilisateur</p>
		<h1 class="sci-page-title">Paramètres du compte</h1>
		<p class="sci-page-subtitle">
			Centralise l’identité du compte, les accès utiles et les zones de conformité sans mélanger cela avec les réglages d’interface.
		</p>
	</header>

	<div class="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Identité du compte</CardTitle>
					<CardDescription>Référence d’accès, posture d’authentification et contexte de travail retenu.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="grid gap-4 pt-0 md:grid-cols-2">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Email</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{email}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Mode d'accès</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{accessMode}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">SCI active</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{activeSciStatus}</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{activeSciDetail}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Page d’ouverture</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{defaultLandingRoute}</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Point d’entrée fonctionnel appliqué au navigateur courant.
					</p>
				</div>
			</CardContent>
		</Card>

		<div class="grid gap-6">
			<Card class="sci-section-card">
				<CardHeader>
					<div>
						<CardTitle class="text-lg">Abonnement et facturation</CardTitle>
						<CardDescription>Capacité active, quotas et accès aux options d’évolution de l’offre.</CardDescription>
					</div>
				</CardHeader>
				<CardContent class="grid gap-3 pt-0">
					{#if subscription}
						<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Offre active</p>
							<p class="mt-2 text-lg font-semibold text-slate-900 dark:text-slate-100">{subscription.plan_name}</p>
							<p class="mt-1 text-slate-500 dark:text-slate-400">
								{subscription.max_scis == null ? 'SCI illimitées' : `${subscription.current_scis}/${subscription.max_scis} SCI`}
								•
								{subscription.max_biens == null ? 'Biens illimités' : `${subscription.current_biens}/${subscription.max_biens} biens`}
							</p>
						</div>
						<div class="grid gap-2 sm:grid-cols-2">
							<Button href="/pricing" class="justify-start">Voir les offres et upgrader</Button>
							<Button href="/scis" variant="outline" class="justify-start">Ouvrir le portefeuille SCI</Button>
						</div>
					{:else if subscriptionError}
						<p class="sci-inline-alert sci-inline-alert-error">{subscriptionError}</p>
					{/if}
				</CardContent>
			</Card>

			<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Sécurité et données</CardTitle>
					<CardDescription>Raccourcis vers les réglages d’interface, la confidentialité et les zones de contrôle du compte.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="grid gap-2 pt-0">
				<Button href="/settings" variant="outline" class="justify-start">Préférences d’interface</Button>
				<Button href="/account/privacy" variant="outline" class="justify-start">Mes données et confidentialité</Button>
				<Button href="/dashboard" variant="outline" class="justify-start">Retour au cockpit</Button>
			</CardContent>
		</Card>
		</div>
	</div>
</section>
