<script lang="ts">
	import { getContext } from 'svelte';
	import type { User } from '@supabase/supabase-js';
	import type { SubscriptionEntitlements } from '$lib/api';
	import { supabase } from '$lib/supabase';
	import WorkspaceActionBar from '$lib/components/WorkspaceActionBar.svelte';
	import WorkspaceHeader from '$lib/components/WorkspaceHeader.svelte';
	import WorkspaceRailCard from '$lib/components/WorkspaceRailCard.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { addToast } from '$lib/components/ui/toast';
	import { getStoredActiveSciId } from '$lib/portfolio/active-sci';
	import { readApplicationPreferences } from '$lib/settings/application-preferences';

	const user = getContext<User>('user');
	const subscription = getContext<SubscriptionEntitlements>('subscription');

	const email = user?.email || 'Compte non connecté';
	const accessMode = user?.email ? 'Connexion par lien sécurisé' : 'Aucune session active';
	const activeSciId = getStoredActiveSciId() || '';
	const defaultLandingRoute = readApplicationPreferences().defaultLandingRoute;

	const activeSciStatus = activeSciId ? 'Une SCI active est mémorisée' : 'Aucune SCI active mémorisée';
	const activeSciDetail = activeSciId ? "L'interface reviendra sur la dernière société suivie." : "Sélectionne une SCI dans le portefeuille pour cadrer les vues métier.";
	const capacityLabel = subscription
		? subscription.max_scis == null
			? 'SCI et biens illimités'
			: `${subscription.current_scis}/${subscription.max_scis} SCI • ${subscription.current_biens}/${subscription.max_biens} biens`
		: "Chargement de l'offre active";

	// Password change
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
</script>

<svelte:head><title>Compte | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<WorkspaceHeader
		eyebrow="Compte • identité, sécurité, abonnement"
		title="Mon compte"
		subtitle="Le compte concentre l'identité de connexion, l'offre active, les quotas et les zones de conformité. Les préférences d'interface restent isolées dans Paramètres."
		contextLabel="Session active"
		contextValue={email}
		contextDetail={subscription ? `${subscription.plan_name} • ${capacityLabel}` : accessMode}
	>
		<Button href="/account/billing">Offre et facturation</Button>
		<Button href="/settings" variant="outline">Paramètres</Button>
		<Button href="/account/privacy" variant="outline">Confidentialité</Button>
	</WorkspaceHeader>

	<WorkspaceActionBar
		eyebrow="Lecture du compte"
		title="Ce que l'on arbitre ici"
		description="Vérifier l'identité de connexion, contrôler la capacité active et retrouver les points de conformité sans mélanger cela avec les réglages locaux du navigateur."
	>
		<div class="sci-action-grid">
			<div class="sci-action-card">
				<p class="sci-action-card-title">Identité</p>
				<p class="sci-action-card-value">{email}</p>
				<p class="sci-action-card-body">Adresse de référence utilisée pour les liens sécurisés.</p>
			</div>
			<div class="sci-action-card">
				<p class="sci-action-card-title">Capacité active</p>
				<p class="sci-action-card-value">{subscription?.plan_name || 'Offre en cours'}</p>
				<p class="sci-action-card-body">{capacityLabel}</p>
			</div>
			<div class="sci-action-card">
				<p class="sci-action-card-title">Point d'entrée</p>
				<p class="sci-action-card-value">{defaultLandingRoute}</p>
				<p class="sci-action-card-body">Page ouverte après connexion sur ce navigateur.</p>
			</div>
		</div>
		<div class="mt-5 sci-primary-actions">
			<Button href="/account/billing">Voir l'offre active</Button>
			<Button href="/settings" variant="outline">Préférences d'interface</Button>
			<Button href="/scis" variant="outline">Ouvrir le portefeuille SCI</Button>
		</div>
		{#snippet aside()}
			<WorkspaceRailCard
				title="Actions rapides"
				description="Les sujets récurrents du compte restent peu nombreux: offre, confidentialité, retour au tableau de bord."
			>
				<div class="grid gap-2">
					<Button href="/account/privacy" variant="outline" class="w-full justify-start">
						Mes données et confidentialité
					</Button>
					<Button href="/dashboard" variant="outline" class="w-full justify-start">
						Retour au tableau de bord
					</Button>
				</div>
			</WorkspaceRailCard>
		{/snippet}
	</WorkspaceActionBar>

	<div class="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Identité et contexte</CardTitle>
					<CardDescription>Référence d'accès, posture d'authentification et contexte de travail retenu.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="grid gap-4 pt-0 md:grid-cols-2">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Email</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{email}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Mode d'accès</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{accessMode}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">SCI active</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{activeSciStatus}</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{activeSciDetail}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Page d'ouverture</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{defaultLandingRoute}</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Point d'entrée fonctionnel appliqué au navigateur courant.
					</p>
				</div>
			</CardContent>
		</Card>

		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Offre active et conformité</CardTitle>
					<CardDescription>Capacité active, quotas et contrôles utiles liés au compte connecté.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="grid gap-3 pt-0">
				{#if subscription}
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
						<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Offre active</p>
						<p class="mt-2 text-lg font-semibold text-slate-900 dark:text-slate-100">{subscription.plan_name}</p>
						<p class="mt-1 text-slate-500 dark:text-slate-400">{capacityLabel}</p>
					</div>
				{/if}

				<div class="grid gap-2">
					<Button href="/account/billing" class="justify-start">Voir les offres et upgrader</Button>
					<Button href="/account/privacy" variant="outline" class="justify-start">Mes données et confidentialité</Button>
					<Button href="/dashboard" variant="outline" class="justify-start">Retour au tableau de bord</Button>
				</div>
			</CardContent>
		</Card>
	</div>

	<Card class="sci-section-card mt-6">
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
</section>
