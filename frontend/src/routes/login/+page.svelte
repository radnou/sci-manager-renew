<script lang="ts">
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

	let email = '';
	let isLoading = false;
	let errorMessage = '';
	let showCheckEmail = false;

	async function handleMagicLink() {
		errorMessage = '';
		isLoading = true;

		const { error } = await supabase.auth.signInWithOtp({
			email: email,
			options: {
				emailRedirectTo: `${window.location.origin}/auth/callback`
			}
		});

		if (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible d’envoyer le lien de connexion.');
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

		isLoading = false;
	}
</script>

<svelte:head>
	<title>Connexion — GererSCI</title>
	<meta name="description" content="Connectez-vous à votre espace GererSCI." />
</svelte:head>

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
		<Card class="sci-section-card">
			<CardHeader>
				<p class="sci-eyebrow">Authentification sans mot de passe</p>
				<CardTitle class="text-2xl">Connexion par lien magique</CardTitle>
				<CardDescription>Recevez un lien de connexion sécurisé par email.</CardDescription>
			</CardHeader>
			<CardContent>
				{#if showCheckEmail}
					<div class="mb-6 rounded-lg bg-emerald-950 p-4 text-emerald-100">
						<p class="font-semibold">✓ Email envoyé!</p>
						<p class="mt-2 text-sm">
							Consultez votre boîte mail à <strong>{email}</strong> et cliquez sur le lien pour vous connecter.
						</p>
					</div>

					<Button href="/" variant="outline" class="w-full">Retour à l'accueil</Button>
				{:else}
					<form class="space-y-4" on:submit|preventDefault={handleMagicLink}>
						<label class="sci-field">
							<span class="sci-field-label">Email</span>
							<Input
								type="email"
								bind:value={email}
								required
								placeholder="vous@sci.fr"
								disabled={isLoading}
							/>
						</label>

						{#if errorMessage}
							<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
						{/if}

						<Button type="submit" class="w-full" disabled={isLoading || !email}>
							{isLoading ? 'Envoi en cours...' : 'Recevoir le lien de connexion'}
						</Button>
					</form>

					<div class="relative mt-6">
						<div class="absolute inset-0 flex items-center">
							<div class="w-full border-t border-slate-700"></div>
						</div>
						<div class="relative flex justify-center text-sm">
							<span class="bg-slate-50 px-2 text-slate-500">ou</span>
						</div>
					</div>

					<Button href="/register" variant="outline" class="mt-6 w-full">Créer un compte</Button>
				{/if}
			</CardContent>
		</Card>
	</div>
</section>
