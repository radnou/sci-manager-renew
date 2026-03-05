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

	let email = $state('');
	let isLoading = $state(false);
	let errorMessage = $state('');
	let showCheckEmail = $state(false);

	async function handleRegister(event: SubmitEvent) {
		event.preventDefault();
		errorMessage = '';
		isLoading = true;

		const { error } = await supabase.auth.signInWithOtp({
			email: email,
			options: {
				emailRedirectTo: `${window.location.origin}/auth/callback`
			}
		});

		if (error) {
			errorMessage = formatApiErrorMessage(error, 'Impossible d’envoyer le lien de création.');
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

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
		<Card class="sci-section-card">
			<CardHeader>
				<p class="sci-eyebrow">Authentification sans mot de passe</p>
				<CardTitle class="text-2xl">Créer un compte</CardTitle>
				<CardDescription>Démarre ton espace GererSCI en moins de 2 minutes.</CardDescription>
			</CardHeader>
			<CardContent>
				{#if showCheckEmail}
					<div class="mb-6 rounded-lg bg-emerald-950 p-4 text-emerald-100">
						<p class="font-semibold">✓ Email envoyé!</p>
						<p class="mt-2 text-sm">
							Consultez votre boîte mail à <strong>{email}</strong> et cliquez sur le lien pour créer
							votre compte.
						</p>
					</div>

					<Button href="/" variant="outline" class="w-full">Retour à l'accueil</Button>
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
							/>
						</label>

						{#if errorMessage}
							<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
						{/if}

						<Button type="submit" class="w-full" disabled={isLoading || !email}>
							{isLoading ? 'Envoi en cours...' : 'Recevoir le lien de création'}
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

					<Button href="/login" variant="outline" class="mt-6 w-full">
						Vous avez déjà un compte?
					</Button>
				{/if}
			</CardContent>
		</Card>
	</div>
</section>
