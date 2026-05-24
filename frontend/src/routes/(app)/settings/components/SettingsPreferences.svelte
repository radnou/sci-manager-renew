<script lang="ts">
	import {
		saveApplicationPreferences,
		type ApplicationLandingRoute,
		type ApplicationPreferences
	} from '$lib/settings/application-preferences';
	import { theme, type ThemePreference } from '$lib/stores/theme';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { addToast } from '$lib/components/ui/toast';

	interface Props {
		preferences: ApplicationPreferences;
		currentTheme: ThemePreference;
	}

	let { preferences = $bindable(), currentTheme = $bindable() }: Props = $props();

	const landingRouteOptions: Array<{ value: ApplicationLandingRoute; label: string }> = [
		{ value: '/dashboard', label: 'Tableau de bord' },
		{ value: '/scis', label: 'Portefeuille' },
		{ value: '/exploitation', label: 'Exploitation' },
		{ value: '/finances', label: 'Finances' },
		{ value: '/settings', label: 'Paramètres' }
	];

	function handleSavePreferences() {
		saveApplicationPreferences(preferences);
		addToast({
			title: 'Paramètres enregistrés',
			description: 'Les préférences ont été mises à jour sur ce navigateur.',
			variant: 'success'
		});
	}
</script>

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

			<!-- Jour de loyer par défaut (global fallback) -->
			<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
				<div class="flex items-start justify-between gap-3">
					<div>
						<p class="font-semibold text-slate-900 dark:text-slate-100">Jour de loyer par défaut</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">Jour du mois auquel les loyers sont générés, sauf surcharge au niveau de la SCI ou du bien (1–28).</p>
					</div>
					<input
						type="number"
						min="1"
						max="28"
						bind:value={preferences.defaultJourLoyer}
						class="w-16 rounded-lg border border-slate-200 bg-white px-2 py-1 text-right text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
						aria-label="Jour de loyer par défaut"
					/>
				</div>
			</div>

			<Button onclick={handleSavePreferences}>Enregistrer les préférences</Button>
		</CardContent>
	</Card>
</div>
