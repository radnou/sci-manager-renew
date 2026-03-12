<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';
	import { addToast } from '$lib/components/ui/toast';

	let loading = $state(true);
	let error = $state(false);

	onMount(async () => {
		try {
			const { data: sessionData, error: sessionError } = await supabase.auth.getSession();

			if (sessionError || !sessionData?.session) {
				error = true;
				addToast({
					title: 'Erreur de connexion',
					description: 'Le lien est invalide ou a expir\u00e9.',
					variant: 'error'
				});
				setTimeout(() => goto('/login'), 3000);
				return;
			}

			// Detect password recovery flow from URL hash
			const hashParams = new URLSearchParams(window.location.hash.substring(1));
			const type = hashParams.get('type');

			if (type === 'recovery') {
				await goto('/reset-password', { replaceState: true });
				return;
			}

			addToast({
				title: 'Connexion r\u00e9ussie',
				description: 'Bienvenue dans votre cockpit SCI.',
				variant: 'success'
			});

			await goto('/dashboard', { replaceState: true });
		} catch {
			error = true;
			addToast({
				title: 'Erreur',
				description: 'Une erreur est survenue. Veuillez r\u00e9essayer.',
				variant: 'error'
			});
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex min-h-screen items-center justify-center px-4">
	<Card class="w-full max-w-md p-8 text-center">
		{#if loading}
			<div class="space-y-4">
				<div
					class="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-slate-200 border-t-blue-500 dark:border-slate-600"
				></div>
				<p class="text-slate-500 dark:text-slate-400">
					V\u00e9rification de votre lien de connexion...
				</p>
			</div>
		{:else if error}
			<div class="space-y-4">
				<p class="font-semibold text-red-600 dark:text-red-400">Lien invalide ou expir\u00e9</p>
				<p class="text-sm text-slate-500 dark:text-slate-400">
					Veuillez r\u00e9essayer. Redirection en cours...
				</p>
				<Button href="/login" class="w-full">Retourner \u00e0 la connexion</Button>
			</div>
		{:else}
			<div class="space-y-4">
				<p class="font-semibold text-emerald-600 dark:text-emerald-400">Connexion r\u00e9ussie</p>
				<p class="text-slate-500 dark:text-slate-400">
					Redirection vers votre tableau de bord...
				</p>
			</div>
		{/if}
	</Card>
</div>
