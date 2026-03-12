<script lang="ts">
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

	let email = $state('');
	let isLoading = $state(false);
	let submitted = $state(false);

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		isLoading = true;

		try {
			await fetch(`${API_URL}/api/v1/auth/forgot-password`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ email })
			});
		} catch {
			// Ignore errors — always show success to prevent email enumeration
		}

		submitted = true;
		isLoading = false;
	}
</script>

<svelte:head>
	<title>Mot de passe oublié — GererSCI</title>
</svelte:head>

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
		<Card class="sci-section-card">
			<CardHeader>
				<p class="sci-eyebrow">Récupération de compte</p>
				<CardTitle class="text-2xl">Mot de passe oublié</CardTitle>
				<CardDescription>
					Entrez votre adresse email pour recevoir un lien de réinitialisation.
				</CardDescription>
			</CardHeader>
			<CardContent>
				{#if submitted}
					<div
						class="mb-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-100"
					>
						<p class="font-semibold">Email envoyé</p>
						<p class="mt-2 text-sm">
							Si un compte existe pour <strong>{email}</strong>, vous recevrez un lien de
							réinitialisation dans quelques instants. Pensez à vérifier vos spams.
						</p>
					</div>

					<div class="space-y-3">
						<Button href="/login" class="w-full">Retour à la connexion</Button>
					</div>
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

						<Button type="submit" class="w-full" disabled={isLoading || !email}>
							{isLoading ? 'Envoi en cours...' : 'Envoyer le lien de réinitialisation'}
						</Button>
					</form>

					<p class="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
						Vous vous souvenez de votre mot de passe ?
						<a
							href="/login"
							class="font-medium text-blue-600 transition-colors hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
						>
							Se connecter
						</a>
					</p>
				{/if}
			</CardContent>
		</Card>
	</div>
</section>
