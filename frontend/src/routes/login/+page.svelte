<script lang="ts">
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
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { trackEvent, EVENTS } from '$lib/analytics';

	type LoginMode = 'password' | 'magic-link';

	let email = $state('');
	let password = $state('');
	let mode = $state<LoginMode>('password');
	let isLoading = $state(false);
	let errorMessage = $state('');
	let showCheckEmail = $state(false);
	let emailTouched = $state(false);
	let passwordTouched = $state(false);
	let submitAttempted = $state(false);
	const isDevMode = import.meta.env.DEV;

	const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	let emailEmpty = $derived(email.trim() === '');
	let emailInvalid = $derived(!emailEmpty && !emailRegex.test(email.trim()));
	let showEmailEmptyError = $derived((emailTouched || submitAttempted) && emailEmpty);
	let showEmailInvalidError = $derived((emailTouched || submitAttempted) && emailInvalid);
	let showPasswordEmptyError = $derived(
		(passwordTouched || submitAttempted) && mode === 'password' && password.length === 0
	);

	function getRedirectTarget(): string {
		const next = page.url.searchParams.get('next');
		return next || '/dashboard';
	}

	async function handlePasswordLogin() {
		trackEvent(EVENTS.LOGIN_START, { mode: 'password' });
		errorMessage = '';
		isLoading = true;

		const { error } = await supabase.auth.signInWithPassword({
			email,
			password
		});

		if (error) {
			errorMessage =
				error.message === 'Invalid login credentials'
					? 'Email ou mot de passe incorrect.'
					: formatApiErrorMessage(error, 'Erreur de connexion.');
		} else {
			trackEvent(EVENTS.LOGIN_SUCCESS);
			goto(getRedirectTarget(), { replaceState: true });
			return;
		}

		isLoading = false;
	}

	async function handleMagicLink() {
		trackEvent(EVENTS.LOGIN_START, { mode: 'magic-link' });
		errorMessage = '';
		isLoading = true;

		try {
			const res = await fetch(`${API_URL}/api/v1/auth/magic-link/send`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email })
			});
			const data = await res.json();

			if (!res.ok || !data.success) {
				errorMessage = data.detail || data.message || "Impossible d'envoyer le lien de connexion.";
				addToast({
					title: 'Erreur',
					description: errorMessage,
					variant: 'error'
				});
			} else {
				showCheckEmail = true;
				addToast({
					title: 'Email envoyé',
					description: `Vérifiez votre boîte mail à ${email}`,
					variant: 'success'
				});
			}
		} catch {
			errorMessage = "Impossible de contacter le serveur. Vérifiez votre connexion.";
			addToast({
				title: 'Erreur',
				description: errorMessage,
				variant: 'error'
			});
		}

		isLoading = false;
	}

	function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		submitAttempted = true;
		errorMessage = '';

		if (emailEmpty) {
			errorMessage = "Veuillez saisir votre adresse email.";
			return;
		}
		if (emailInvalid) {
			errorMessage = "Veuillez saisir une adresse email valide.";
			return;
		}
		if (mode === 'password' && password.length === 0) {
			errorMessage = "Veuillez saisir votre mot de passe.";
			return;
		}

		if (mode === 'password') {
			handlePasswordLogin();
		} else {
			handleMagicLink();
		}
	}
</script>

<svelte:head>
	<title>Connexion — GérerSCI</title>
	<meta name="robots" content="noindex, nofollow" />
	<link rel="canonical" href="https://gerersci.fr/login" />
</svelte:head>

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
		<h1 class="sr-only">Connexion à GérerSCI</h1>
	<Card class="sci-section-card">
			<CardHeader>
				<p class="sci-eyebrow">Espace de gestion</p>
				<CardTitle class="text-2xl">Connexion</CardTitle>
				<CardDescription>Accédez à votre espace de gestion SCI.</CardDescription>
			</CardHeader>
			<CardContent>
				{#if showCheckEmail}
					<div
						class="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-100"
					>
						<p class="font-semibold">Lien envoyé</p>
						<p class="mt-2 text-sm">
							Consultez votre boîte mail à <strong>{email}</strong> et cliquez sur le lien
							pour vous connecter.
						</p>
					</div>

					{#if isDevMode}
						<div
							class="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-100"
						>
							<p class="text-sm font-semibold">Mode développement</p>
							<p class="mt-1 text-sm">
								En mode développement, le lien magique n'est pas envoyé par email.
								Consultez les logs du backend (<code class="rounded bg-amber-100 px-1 dark:bg-amber-900">docker compose logs backend</code>) pour retrouver le lien.
							</p>
						</div>
					{/if}

					<Button href="/" variant="outline" class="w-full">Retour à l'accueil</Button>
				{:else}
					<form class="space-y-4" onsubmit={handleSubmit} novalidate>
						<label class="sci-field">
							<span class="sci-field-label">Email</span>
							<Input
								type="email"
								bind:value={email}
								required
								placeholder="vous@sci.fr"
								disabled={isLoading}
								autocomplete="email"
								aria-invalid={showEmailEmptyError || showEmailInvalidError}
								aria-describedby={showEmailEmptyError ? 'login-email-empty' : showEmailInvalidError ? 'login-email-invalid' : undefined}
								onblur={() => (emailTouched = true)}
							/>
							{#if showEmailEmptyError}
								<span id="login-email-empty" role="alert" class="mt-1 text-xs text-red-600 dark:text-red-400">
									L'email est requis.
								</span>
							{:else if showEmailInvalidError}
								<span id="login-email-invalid" role="alert" class="mt-1 text-xs text-red-600 dark:text-red-400">
									Adresse email invalide (ex : vous@sci.fr).
								</span>
							{/if}
						</label>

						{#if mode === 'password'}
							<label class="sci-field">
								<span class="sci-field-label">Mot de passe</span>
								<Input
									type="password"
									bind:value={password}
									required
									placeholder="••••••••"
									disabled={isLoading}
									autocomplete="current-password"
									aria-invalid={showPasswordEmptyError}
									onblur={() => (passwordTouched = true)}
								/>
								{#if showPasswordEmptyError}
									<span role="alert" class="mt-1 text-xs text-red-600 dark:text-red-400">
										Le mot de passe est requis.
									</span>
								{/if}
							</label>

							<div class="flex justify-end">
								<a
									href="/forgot-password"
									class="text-sm text-blue-600 transition-colors hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
								>
									Mot de passe oublié ?
								</a>
							</div>
						{/if}

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
							disabled={isLoading}
						>
							{#if isLoading}
								{mode === 'password' ? 'Connexion en cours...' : 'Envoi en cours...'}
							{:else}
								{mode === 'password' ? 'Se connecter' : 'Recevoir le lien de connexion'}
							{/if}
						</Button>
					</form>

					<!-- Mode toggle -->
					<div class="relative mt-6">
						<div class="absolute inset-0 flex items-center">
							<div
								class="w-full border-t border-slate-200 dark:border-slate-700"
							></div>
						</div>
						<div class="relative flex justify-center text-sm">
							<span
								class="bg-white px-2 text-slate-500 dark:bg-slate-950 dark:text-slate-400"
								>ou</span
							>
						</div>
					</div>

					<div class="mt-6 space-y-3">
						{#if mode === 'password'}
							<Button
								variant="outline"
								class="w-full"
								onclick={() => {
									mode = 'magic-link';
									errorMessage = '';
								}}
							>
								Connexion par lien magique
							</Button>
						{:else}
							<Button
								variant="outline"
								class="w-full"
								onclick={() => {
									mode = 'password';
									errorMessage = '';
								}}
							>
								Connexion par mot de passe
							</Button>
						{/if}
					</div>

					<p class="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
						Pas encore de compte ?
						<a
							href="/register"
							class="font-medium text-blue-600 transition-colors hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
						>
							Créer un compte
						</a>
					</p>
				{/if}
			</CardContent>
		</Card>
	</div>
</section>
