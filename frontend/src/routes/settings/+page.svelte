<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchSubscriptionEntitlements, type SubscriptionEntitlements } from '$lib/api';
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
		{ value: '/dashboard', label: 'Cockpit' },
		{ value: '/scis', label: 'Portefeuille SCI' },
		{ value: '/loyers', label: 'Suivi des loyers' },
		{ value: '/settings', label: "Paramètres de l'application" }
	];

	let preferences: ApplicationPreferences = { ...DEFAULT_APPLICATION_PREFERENCES };
	let subscription: SubscriptionEntitlements | null = null;
	let subscriptionError = '';

	$: landingRouteLabel =
		landingRouteOptions.find((option) => option.value === preferences.defaultLandingRoute)?.label ??
		'Cockpit';

	onMount(async () => {
		preferences = readApplicationPreferences();
		try {
			subscription = await fetchSubscriptionEntitlements();
		} catch (error) {
			subscriptionError = formatApiErrorMessage(
				error,
				"Impossible de charger l'offre active."
			);
		}
	});

	function handleSave() {
		saveApplicationPreferences(preferences);
		addToast({
			title: 'Paramètres enregistrés',
			description: "Les préférences d'application ont été mises à jour sur ce navigateur.",
			variant: 'success'
		});
	}
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Réglages • Expérience opérateur</p>
		<h1 class="sci-page-title">Paramètres de l'application</h1>
		<p class="sci-page-subtitle">
			Règle le point d’entrée, la densité d’affichage, la prévisualisation PDF et les alertes de ton espace de pilotage.
		</p>
	</header>

	<div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Préférences d'expérience</CardTitle>
					<CardDescription>Ces réglages sont propres au navigateur courant et s’appliquent à tout l’espace connecté.</CardDescription>
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

				<div class="grid gap-3 md:grid-cols-3">
					<label class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
						<div class="flex items-start justify-between gap-3">
							<div>
								<p class="font-semibold text-slate-900 dark:text-slate-100">Prévisualisation PDF</p>
								<p class="mt-1 text-slate-500 dark:text-slate-400">Affiche les quittances directement dans l’interface.</p>
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

				<Button onclick={handleSave}>Enregistrer les paramètres</Button>
			</CardContent>
		</Card>

		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Impact des réglages</CardTitle>
					<CardDescription>Lecture immédiate de la configuration active sur ce navigateur, sans mélanger cela avec les actions de compte.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="grid gap-3 pt-0">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Point d’entrée</p>
					<p class="mt-2 text-base font-semibold text-slate-900 dark:text-slate-100">{landingRouteLabel}</p>
					<p class="mt-1 text-slate-500 dark:text-slate-400">La première page ouverte après connexion sur ce navigateur.</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Densité d’affichage</p>
					<p class="mt-2 text-base font-semibold text-slate-900 dark:text-slate-100">{preferences.density === 'compact' ? 'Compacte' : 'Confortable'}</p>
					<p class="mt-1 text-slate-500 dark:text-slate-400">
						{preferences.density === 'compact'
							? 'Priorise la densité d’information pour les revues opérateur.'
							: 'Laisse davantage d’air entre les blocs pour un pilotage confortable.'}
					</p>
				</div>
				<div class="grid gap-3 md:grid-cols-2">
					<div class="rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-950">
						<p class="font-semibold text-slate-900 dark:text-slate-100">PDF</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							{preferences.showPdfPreview ? 'Prévisualisation intégrée active.' : 'Téléchargement sans preview priorisé.'}
						</p>
					</div>
					<div class="rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-950">
						<p class="font-semibold text-slate-900 dark:text-slate-100">Alertes</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							{preferences.riskAlertsEnabled ? 'Les signaux de risque sont mis en avant.' : 'Les vues restent neutres sans priorisation des risques.'}
						</p>
					</div>
				</div>
				{#if subscription}
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Capacité active</p>
						<p class="mt-2 text-base font-semibold text-slate-900 dark:text-slate-100">{subscription.plan_name}</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">
							{subscription.max_scis == null ? 'SCI illimitées' : `${subscription.remaining_scis ?? 0} SCI restantes`}
							•
							{subscription.max_biens == null ? 'Biens illimités' : `${subscription.remaining_biens ?? 0} biens restants`}
						</p>
					</div>
				{:else if subscriptionError}
					<p class="sci-inline-alert sci-inline-alert-error">{subscriptionError}</p>
				{/if}
				<div class="grid gap-2 border-t border-slate-200 pt-3 dark:border-slate-800">
					<Button href="/account" variant="outline" class="justify-start">Aller au compte</Button>
					<Button href="/dashboard" variant="outline" class="justify-start">Retour au cockpit</Button>
				</div>
			</CardContent>
		</Card>
	</div>
</section>
