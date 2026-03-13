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

	type LoginMode = 'password' | 'magic-link';

	let email = $state('');
	let password = $state('');
	let mode = $state<LoginMode>('password');
	let isLoading = $state(false);
	let errorMessage = $state('');
	let showCheckEmail = $state(false);

	function getRedirectTarget(): string {
		const next = page.url.searchParams.get('next');
		return next || '/dashboard';
	}

	async function handlePasswordLogin() {
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
			goto(getRedirectTarget(), { replaceState: true });
			return;
		}

		isLoading = false;
	}

	async function handleMagicLink() {
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
		if (mode === 'password') {
			handlePasswordLogin();
		} else {
			handleMagicLink();
		}
	}
</script>

<svelte:head>
	<title>Connexion — GererSCI</title>
</svelte:head>

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
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

					<Button href="/" variant="outline" class="w-full">Retour à l'accueil</Button>
				{:else}
					<form class="space-y-4" onsubmit={handleSubmit}>
						<label class="sci-field">
							<span class="sci-field-label">Email</span>
							<Input
								type="email"
								bind:value={email}
								required
								placeholder="vous@sci.fr"
								disabled={isLoading}
								autocomplete="email"
							/>
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
								/>
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
							disabled={isLoading || !email || (mode === 'password' && !password)}
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
							Créer un compte gratuit
						</a>
					</p>
				{/if}
			</CardContent>
		</Card>
	</div>
</section>
