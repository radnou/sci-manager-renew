<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
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

	let email = $state('');
	let password = $state('');
	let passwordConfirm = $state('');
	let isLoading = $state(false);
	let errorMessage = $state('');
	let showConfirmEmail = $state(false);

	const planLabels: Record<string, { name: string; features: string }> = {
		starter: { name: 'Gestion', features: '1 SCI, 5 biens, quittances PDF, CERFA 2044' },
		pro: { name: 'Pilotage', features: 'SCI illimitées, CERFA 2044, fiscalité complète' },
		lifetime: { name: 'Fondateur', features: 'Tout Pilotage inclus — à vie' },
	};
	const selectedPlan = $derived(page.url?.searchParams.get('plan') ?? null);
	const planLabel = $derived(selectedPlan ? planLabels[selectedPlan] ?? null : null);

	const passwordMinLength = 8;

	let passwordMismatch = $derived(
		passwordConfirm.length > 0 && password !== passwordConfirm
	);

	let passwordTooShort = $derived(
		password.length > 0 && password.length < passwordMinLength
	);

	let consentCgu = $state(false);

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
		trackEvent(EVENTS.REGISTER_START);

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
			trackEvent(EVENTS.REGISTER_SUCCESS);
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
	<title>Inscription — GérerSCI</title>
	<meta name="robots" content="noindex, nofollow" />
	<link rel="canonical" href="https://gerersci.fr/register" />
</svelte:head>

<section class="sci-page-shell">
	<div class="mx-auto mt-6 w-full max-w-md">
		<h1 class="sr-only">Inscription à GérerSCI</h1>
	<Card class="sci-section-card">
			<CardHeader>
				{#if selectedPlan && planLabel}
					<Badge variant="secondary" class="mb-2 w-fit text-xs">Aucune carte bancaire requise</Badge>
					<CardTitle class="text-2xl">Voyez ce que donnerait votre SCI dans un vrai cockpit de gestion.</CardTitle>
					<CardDescription>
						Données de démo pré-remplies. Zéro carte bancaire. 2 minutes pour comprendre.
					</CardDescription>
				{:else}
					<p class="sci-eyebrow">Créer un compte</p>
					<CardTitle class="text-2xl">Créez votre compte</CardTitle>
					<CardDescription>
						Explorez GérerSCI avec des données de démonstration.
					</CardDescription>
				{/if}
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
								<span role="alert" class="mt-1 text-xs text-amber-600 dark:text-amber-400">
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
								<span role="alert" class="mt-1 text-xs text-red-600 dark:text-red-400">
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

						<label class="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-400">
							<input
								type="checkbox"
								bind:checked={consentCgu}
								required
								class="mt-0.5 rounded border-slate-300"
							/>
							<span>
								J'ai lu et j'accepte les
								<a href="/cgu" class="text-blue-600 underline hover:text-blue-800 dark:text-blue-400">CGU</a>
								et la
								<a href="/confidentialite" class="text-blue-600 underline hover:text-blue-800 dark:text-blue-400">politique de confidentialité</a>.
							</span>
						</label>

						<Button
							type="submit"
							class="w-full"
							disabled={isLoading || !email || !password || !passwordConfirm || passwordMismatch || passwordTooShort || !consentCgu}
						>
							{isLoading ? 'Inscription en cours...' : "S'inscrire"}
						</Button>
					</form>

					{#if selectedPlan && planLabels[selectedPlan]}
						<div class="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm dark:border-blue-800 dark:bg-blue-950/30">
							<p class="font-medium text-blue-800 dark:text-blue-300">
								Plan retenu : {planLabels[selectedPlan].name}
							</p>
							<p class="mt-1 text-blue-600 dark:text-blue-400">
								{planLabels[selectedPlan].features}
							</p>
							<p class="mt-1 text-xs text-blue-500 dark:text-blue-500">
								Activable après exploration. Annulable sous 30 jours.
							</p>
						</div>
					{/if}

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
						<a href="/cgu" class="underline hover:text-slate-700 dark:hover:text-slate-300">CGU</a>
						et notre
						<a href="/confidentialite" class="underline hover:text-slate-700 dark:hover:text-slate-300">politique de confidentialité</a>.
					</p>
				{/if}
			</CardContent>
		</Card>
	</div>
</section>
