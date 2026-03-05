<script lang="ts">
	import { onMount } from 'svelte';
	import { getCurrentSession } from '$lib/auth/session';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { getStoredActiveSciId } from '$lib/portfolio/active-sci';
	import { readApplicationPreferences } from '$lib/settings/application-preferences';

	let email = 'Compte non connecté';
	let accessMode = 'Session sécurisée';
	let activeSciId = '';
	let defaultLandingRoute = '/dashboard';

	onMount(async () => {
		const session = await getCurrentSession();
		email = session?.user?.email || 'Compte non connecté';
		accessMode = session?.user?.email ? 'Connexion par lien sécurisé' : 'Aucune session active';
		activeSciId = getStoredActiveSciId() || '';
		defaultLandingRoute = readApplicationPreferences().defaultLandingRoute;
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

	<div class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Identité du compte</CardTitle>
					<CardDescription>Référence d’accès, contexte SCI actif et point d’entrée préféré.</CardDescription>
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
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{activeSciId ? 'Une SCI active est mémorisée pour ce navigateur' : 'Aucune SCI active mémorisée'}
					</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">Page d’ouverture</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{defaultLandingRoute}</p>
				</div>
			</CardContent>
		</Card>

		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Actions de compte</CardTitle>
					<CardDescription>Les raccourcis critiques pour gérer la sécurité, les données et la configuration.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="grid gap-2 pt-0">
				<Button href="/settings" variant="outline" class="justify-start">Paramètres de l'application</Button>
				<Button href="/account/privacy" variant="outline" class="justify-start">Mes données et confidentialité</Button>
				<Button href="/scis" variant="outline" class="justify-start">Revenir au portefeuille SCI</Button>
				<Button href="/dashboard" variant="outline" class="justify-start">Retour au cockpit</Button>
			</CardContent>
		</Card>
	</div>
</section>
