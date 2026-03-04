<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';
	import { addToast } from '$lib/components/ui/toast';

	let loading = true;
	let error = false;

	onMount(async () => {
		try {
			// Supabase automatically handles the magic link verification
			// from the URL and sets the session
			const { data: session, error: sessionError } = await supabase.auth.getSession();

			if (sessionError || !session) {
				error = true;
				addToast({
					title: 'Erreur de connexion',
					description: 'Le lien est invalide ou a expiré.',
					variant: 'error'
				});
				setTimeout(() => {
					goto('/login');
				}, 3000);
				return;
			}

			addToast({
				title: 'Connexion réussie',
				description: 'Bienvenue dans votre cockpit SCI.',
				variant: 'success'
			});

			// Redirect to dashboard after successful auth
			await goto('/dashboard');
		} catch (err) {
			error = true;
			addToast({
				title: 'Erreur',
				description: 'Une erreur est survenue. Veuillez réessayer.',
				variant: 'error'
			});
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex min-h-screen items-center justify-center bg-slate-900 px-4">
	<Card class="w-full max-w-md p-8 text-center">
		{#if loading}
			<div class="space-y-4">
				<div class="h-12 w-12 animate-spin rounded-full border-4 border-slate-600 border-t-blue-500 mx-auto"></div>
				<p class="text-slate-400">Vérification de votre lien de connexion...</p>
			</div>
		{:else if error}
			<div class="space-y-4">
				<p class="text-red-500 font-semibold">✗ Lien invalide ou expiré</p>
				<p class="text-slate-400 text-sm">Veuillez réessayer. Vous allez être redirigé...</p>
				<Button href="/login" class="w-full">
					Retourner à la connexion
				</Button>
			</div>
		{:else}
			<div class="space-y-4">
				<p class="text-emerald-500 font-semibold">✓ Connexion réussie!</p>
				<p class="text-slate-400">Vous allez être redirigé vers votre tableau de bord...</p>
			</div>
		{/if}
	</Card>
</div>
