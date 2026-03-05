<script lang="ts">
	import { onMount } from 'svelte';
	import { addToast } from '$lib/components/ui/toast';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
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

	onMount(() => {
		preferences = readApplicationPreferences();
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
					<CardTitle class="text-lg">Raccourcis utiles</CardTitle>
					<CardDescription>Accès rapide aux zones structurantes du compte connecté.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="grid gap-2 pt-0">
				<Button href="/scis" variant="outline" class="justify-start">Ouvrir le portefeuille SCI</Button>
				<Button href="/account" variant="outline" class="justify-start">Paramètres du compte</Button>
				<Button href="/account/privacy" variant="outline" class="justify-start">Confidentialité et données</Button>
				<Button href="/dashboard" variant="outline" class="justify-start">Retour au cockpit</Button>
			</CardContent>
		</Card>
	</div>
</section>
