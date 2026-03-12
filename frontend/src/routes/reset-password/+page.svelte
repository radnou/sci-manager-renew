<script lang="ts">
	import { onMount } from 'svelte';
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

	let password = $state('');
	let passwordConfirm = $state('');
	let isLoading = $state(false);
	let errorMessage = $state('');
	let hasSession = $state(false);
	let checking = $state(true);

	const passwordMinLength = 8;

	let passwordMismatch = $derived(
		passwordConfirm.length > 0 && password !== passwordConfirm
	);

	let passwordTooShort = $derived(
		password.length > 0 && password.length < passwordMinLength
	);

	onMount(async () => {
		const { data } = await supabase.auth.getSession();
		hasSession = !!data?.session;
		checking = false;

		if (!hasSession) {
			errorMessage = "Session expir\u00e9e. Veuillez redemander un lien de r\u00e9initialisation.";
		}
	});

	async function handleReset(event: SubmitEvent) {
		event.preventDefault();
		errorMessage = '';

		if (password !== passwordConfirm) {
			errorMessage = 'Les mots de passe ne correspondent pas.';
			return;
		}

		if (password.length < passwordMinLength) {
			errorMessage = `Le mot de passe doit contenir au moins ${passwordMinLength} caract\u00e8res.`;
			return;
		}

		isLoading = true;

		const { error } = await supabase.auth.updateUser({ password });

		if (error) {
			errorMessage = 'Erreur lors de la mise \u00e0 jour du mot de passe. Veuillez r\u00e9essayer.';
			isLoading = false;
			return;
		}

		addToast({
			title: 'Mot de passe mis \u00e0 jour',
			description: 'Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.',
			variant: 'success'
		});

		goto('/dashboard', { replaceState: true });
	}
</script>

<svelte:head>
	<title>R\u00e9initialiser le mot de passe — GererSCI</title>
</svelte:head>

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
		<Card class="sci-section-card">
			<CardHeader>
				<p class="sci-eyebrow">S\u00e9curit\u00e9 du compte</p>
				<CardTitle class="text-2xl">Nouveau mot de passe</CardTitle>
				<CardDescription>
					Choisissez un nouveau mot de passe pour votre compte.
				</CardDescription>
			</CardHeader>
			<CardContent>
				{#if checking}
					<div class="flex items-center justify-center py-8">
						<div
							class="h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"
						></div>
					</div>
				{:else if !hasSession}
					<p
						role="alert"
						class="mb-6 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300"
					>
						{errorMessage}
					</p>
					<Button href="/forgot-password" class="w-full">
						Demander un nouveau lien
					</Button>
				{:else}
					<form class="space-y-4" onsubmit={handleReset}>
						<label class="sci-field">
							<span class="sci-field-label">Nouveau mot de passe</span>
							<Input
								type="password"
								bind:value={password}
								required
								minlength={passwordMinLength}
								placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
								disabled={isLoading}
								autocomplete="new-password"
							/>
							{#if passwordTooShort}
								<span class="mt-1 text-xs text-amber-600 dark:text-amber-400">
									{passwordMinLength} caract\u00e8res minimum
								</span>
							{/if}
						</label>

						<label class="sci-field">
							<span class="sci-field-label">Confirmer le nouveau mot de passe</span>
							<Input
								type="password"
								bind:value={passwordConfirm}
								required
								minlength={passwordMinLength}
								placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
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
							{isLoading ? 'Mise \u00e0 jour...' : 'Mettre \u00e0 jour le mot de passe'}
						</Button>
					</form>
				{/if}
			</CardContent>
		</Card>
	</div>
</section>
