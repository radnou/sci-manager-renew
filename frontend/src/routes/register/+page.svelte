<script lang="ts">
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';
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

	let email = $state('');
	let password = $state('');
	let passwordConfirm = $state('');
	let isLoading = $state(false);
	let errorMessage = $state('');
	let showConfirmEmail = $state(false);

	const passwordMinLength = 8;

	let passwordMismatch = $derived(
		passwordConfirm.length > 0 && password !== passwordConfirm
	);

	let passwordTooShort = $derived(
		password.length > 0 && password.length < passwordMinLength
	);

	async function handleRegister(event: SubmitEvent) {
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

		const { error } = await supabase.auth.signUp({
			email,
			password,
			options: {
				emailRedirectTo: `${window.location.origin}/auth/callback`
			}
		});

		if (error) {
			if (error.message.includes('already registered')) {
				errorMessage = 'Un compte existe déjà avec cet email. Essayez de vous connecter.';
			} else {
				errorMessage = formatApiErrorMessage(error, "Erreur lors de l'inscription.");
			}
		} else {
			showConfirmEmail = true;
			addToast({
				title: 'Inscription réussie',
				description: 'Vérifiez votre boîte mail pour confirmer votre compte.',
				variant: 'success'
			});
		}

		isLoading = false;
	}
</script>

<svelte:head>
	<title>Inscription — GererSCI</title>
</svelte:head>

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
		<Card class="sci-section-card">
			<CardHeader>
				<p class="sci-eyebrow">Plan Essentiel — Gratuit</p>
				<CardTitle class="text-2xl">Créer un compte</CardTitle>
				<CardDescription>
					Gérez jusqu'à 1 SCI et 2 biens gratuitement. Passez à un plan supérieur quand vous voulez.
				</CardDescription>
			</CardHeader>
			<CardContent>
				{#if showConfirmEmail}
					<div
						class="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-100"
					>
						<p class="font-semibold">Vérifiez votre email</p>
						<p class="mt-2 text-sm">
							Un email de confirmation a été envoyé à <strong>{email}</strong>.
							Cliquez sur le lien pour activer votre compte.
						</p>
					</div>

					<Button href="/login" variant="outline" class="w-full">Aller à la connexion</Button>
				{:else}
					<form class="space-y-4" onsubmit={handleRegister}>
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
							disabled={isLoading || !email || !password || !passwordConfirm || passwordMismatch || passwordTooShort}
						>
							{isLoading ? 'Inscription en cours...' : "S'inscrire gratuitement"}
						</Button>
					</form>

					<p class="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
						Déjà un compte ?
						<a
							href="/login"
							class="font-medium text-blue-600 transition-colors hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
						>
							Se connecter
						</a>
					</p>

					<p class="mt-4 text-center text-xs text-slate-500 dark:text-slate-500">
						En vous inscrivant, vous acceptez nos
						<a href="/cgu" class="underline hover:text-slate-700 dark:hover:text-slate-300">CGU</a>
						et notre
						<a href="/confidentialite" class="underline hover:text-slate-700 dark:hover:text-slate-300">politique de confidentialité</a>.
					</p>
				{/if}
			</CardContent>
		</Card>
	</div>
</section>
