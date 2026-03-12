<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { supabase } from '$lib/supabase';
	import { API_URL } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { addToast } from '$lib/components/ui/toast';

	type WelcomeStep = 'activating' | 'set-password' | 'error';

	let step = $state<WelcomeStep>('activating');
	let errorMessage = $state('');
	let planKey = $state('');
	let password = $state('');
	let passwordConfirm = $state('');
	let isLoading = $state(false);

	const passwordMinLength = 8;

	let passwordMismatch = $derived(
		passwordConfirm.length > 0 && password !== passwordConfirm
	);

	let passwordTooShort = $derived(
		password.length > 0 && password.length < passwordMinLength
	);

	const planLabels: Record<string, string> = {
		starter: 'Gestion',
		pro: 'Fiscal',
		free: 'Essentiel'
	};

	onMount(async () => {
		const sessionId = page.url.searchParams.get('session_id');

		if (!sessionId) {
			// If user is already authenticated, redirect to dashboard
			const {
				data: { session }
			} = await supabase.auth.getSession();
			if (session) {
				goto('/dashboard', { replaceState: true });
				return;
			}
			errorMessage = 'Lien invalide : aucun identifiant de session.';
			step = 'error';
			return;
		}

		try {
			const res = await fetch(
				`${API_URL}/api/v1/auth/activate?session_id=${encodeURIComponent(sessionId)}`
			);
			const data = await res.json();

			if (!res.ok) {
				errorMessage = data.error || "Erreur lors de l'activation du compte.";
				step = 'error';
				return;
			}

			planKey = data.plan_key || '';

			// Exchange token_hash for a Supabase session via verifyOtp
			const { error: otpError } = await supabase.auth.verifyOtp({
				token_hash: data.token_hash,
				type: 'magiclink'
			});

			if (otpError) {
				errorMessage = "Erreur d'authentification. Veuillez réessayer ou contacter le support.";
				step = 'error';
				return;
			}

			step = 'set-password';
		} catch {
			errorMessage = 'Impossible de contacter le serveur. Vérifiez votre connexion.';
			step = 'error';
		}
	});

	async function handleSetPassword(event: SubmitEvent) {
		event.preventDefault();
		errorMessage = '';

		if (password !== passwordConfirm) {
			errorMessage = 'Les mots de passe ne correspondent pas.';
			return;
		}

		if (password.length < passwordMinLength) {
			errorMessage = `Le mot de passe doit contenir au moins ${passwordMinLength} caractères.`;
			return;
		}

		isLoading = true;

		const { error } = await supabase.auth.updateUser({ password });

		if (error) {
			errorMessage = 'Erreur lors de la définition du mot de passe. Veuillez réessayer.';
			isLoading = false;
			return;
		}

		addToast({
			title: 'Bienvenue !',
			description: `Votre compte ${planLabels[planKey] || planKey} est activé.`,
			variant: 'success'
		});

		goto('/onboarding', { replaceState: true });
	}
</script>

<svelte:head>
	<title>Bienvenue — GererSCI</title>
</svelte:head>

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
		{#if step === 'activating'}
			<Card class="sci-section-card">
				<CardHeader>
					<p class="sci-eyebrow">Activation en cours</p>
					<CardTitle class="text-2xl">Préparation de votre espace</CardTitle>
					<CardDescription>Veuillez patienter quelques instants...</CardDescription>
				</CardHeader>
				<CardContent>
					<div class="flex items-center justify-center py-8">
						<div
							class="h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"
						></div>
					</div>
				</CardContent>
			</Card>
		{:else if step === 'set-password'}
			<Card class="sci-section-card">
				<CardHeader>
					<p class="sci-eyebrow">Plan {planLabels[planKey] || planKey} activé</p>
					<CardTitle class="text-2xl">Définissez votre mot de passe</CardTitle>
					<CardDescription>
						Choisissez un mot de passe pour accéder à votre espace de gestion.
					</CardDescription>
				</CardHeader>
				<CardContent>
					<form class="space-y-4" onsubmit={handleSetPassword}>
						<label class="sci-field">
							<span class="sci-field-label">Mot de passe</span>
							<Input
								type="password"
								bind:value={password}
								required
								minlength={passwordMinLength}
								placeholder="••••••••"
								disabled={isLoading}
								autocomplete="new-password"
							/>
							{#if passwordTooShort}
								<span class="mt-1 text-xs text-amber-600 dark:text-amber-400">
									{passwordMinLength} caractères minimum
								</span>
							{/if}
						</label>

						<label class="sci-field">
							<span class="sci-field-label">Confirmer le mot de passe</span>
							<Input
								type="password"
								bind:value={passwordConfirm}
								required
								minlength={passwordMinLength}
								placeholder="••••••••"
								disabled={isLoading}
								autocomplete="new-password"
							/>
							{#if passwordMismatch}
								<span class="mt-1 text-xs text-red-600 dark:text-red-400">
									Les mots de passe ne correspondent pas
								</span>
							{/if}
						</label>

						{#if errorMessage}
							<p
								role="alert"
								class="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300"
							>
								{errorMessage}
							</p>
						{/if}

						<Button
							type="submit"
							class="w-full"
							disabled={isLoading || !password || !passwordConfirm || passwordMismatch || passwordTooShort}
						>
							{isLoading ? 'Activation...' : 'Activer mon compte'}
						</Button>
					</form>
				</CardContent>
			</Card>
		{:else}
			<Card class="sci-section-card">
				<CardHeader>
					<p class="sci-eyebrow">Problème d'activation</p>
					<CardTitle class="text-2xl">Une erreur est survenue</CardTitle>
				</CardHeader>
				<CardContent>
					<p
						role="alert"
						class="mb-6 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300"
					>
						{errorMessage}
					</p>

					<div class="space-y-3">
						<Button href="/pricing" class="w-full">Voir les offres</Button>
						<Button href="/login" variant="outline" class="w-full">Se connecter</Button>
					</div>
				</CardContent>
			</Card>
		{/if}
	</div>
</section>
