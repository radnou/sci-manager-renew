<script lang="ts">
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { addToast } from '$lib/components/ui/toast';

	let email = '';
	let password = '';
	let isLoading = false;
	let errorMessage = '';

	async function handleLogin() {
		errorMessage = '';
		isLoading = true;

		const { error } = await supabase.auth.signInWithPassword({ email, password });
		if (error) {
			errorMessage = error.message;
			addToast({
				title: 'Connexion impossible',
				description: error.message,
				variant: 'error'
			});
			isLoading = false;
			return;
		}

		addToast({
			title: 'Connexion réussie',
			description: 'Bienvenue dans votre cockpit SCI.',
			variant: 'success'
		});
		await goto('/dashboard');
	}
</script>

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
		<Card class="sci-section-card">
			<CardHeader>
				<p class="sci-eyebrow">Authentification</p>
				<CardTitle class="text-2xl">Connexion</CardTitle>
				<CardDescription>Accédez à votre tableau de bord de gestion SCI.</CardDescription>
			</CardHeader>
			<CardContent>
				<form class="space-y-4" on:submit|preventDefault={handleLogin}>
					<label class="sci-field">
						<span class="sci-field-label">Email</span>
						<Input type="email" bind:value={email} required placeholder="vous@sci.fr" />
					</label>
					<label class="sci-field">
						<span class="sci-field-label">Mot de passe</span>
						<Input type="password" bind:value={password} required placeholder="••••••••" />
					</label>

					{#if errorMessage}
						<p class="sci-inline-alert sci-inline-alert-error">{errorMessage}</p>
					{/if}

					<Button type="submit" class="w-full" disabled={isLoading}>
						{isLoading ? 'Connexion...' : 'Se connecter'}
					</Button>
				</form>
			</CardContent>
		</Card>
	</div>
</section>
