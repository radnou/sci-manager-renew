<script lang="ts">
	import { onMount } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';

	let showBanner = $state(false);
	let consentGiven = $state(false);

	const CONSENT_KEY = 'sci_manager_cookie_consent';

	onMount(() => {
		// Vérifier si le consentement a déjà été donné
		const savedConsent = localStorage.getItem(CONSENT_KEY);
		if (savedConsent) {
			consentGiven = true;
			showBanner = false;
		} else {
			// Afficher le banner après un court délai pour meilleure UX
			setTimeout(() => {
				showBanner = true;
			}, 1000);
		}
	});

	function acceptAll() {
		const consent = {
			necessary: true,  // Toujours true
			analytics: false,  // Pas d'analytics pour l'instant
			marketing: false,  // Pas de marketing
			timestamp: Date.now()
		};

		localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
		consentGiven = true;
		showBanner = false;
	}

	function acceptNecessary() {
		const consent = {
			necessary: true,
			analytics: false,
			marketing: false,
			timestamp: Date.now()
		};

		localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
		consentGiven = true;
		showBanner = false;
	}
</script>

{#if showBanner && !consentGiven}
	<div
		class="fixed bottom-0 left-0 right-0 z-50 p-4 sm:p-6 animate-in slide-in-from-bottom duration-300"
		role="dialog"
		aria-live="polite"
		aria-label="Cookie consent banner"
	>
		<Card class="mx-auto max-w-4xl border-2 shadow-2xl bg-white dark:bg-slate-900">
			<div class="p-4 sm:p-6">
				<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
					<div class="flex-1 space-y-2">
						<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
							🍪 Gestion des cookies
						</h2>
						<p class="text-sm text-slate-600 dark:text-slate-400">
							Nous utilisons uniquement des <strong>cookies essentiels</strong> pour votre authentification
							et le fonctionnement du service. Aucun tracking publicitaire ou analytics.
						</p>
						<p class="text-xs text-slate-500 dark:text-slate-500">
							En continuant, vous acceptez l'utilisation de cookies techniques nécessaires au service.
							<a href="/privacy" class="text-blue-600 dark:text-blue-400 hover:underline ml-1">
								En savoir plus →
							</a>
						</p>
					</div>

					<div class="flex flex-col gap-2 sm:flex-row sm:items-center">
						<Button
							variant="outline"
							size="sm"
							onclick={acceptNecessary}
							class="whitespace-nowrap"
						>
							Cookies essentiels uniquement
						</Button>
						<Button
							size="sm"
							onclick={acceptAll}
							class="whitespace-nowrap bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white border-0"
						>
							Tout accepter
						</Button>
					</div>
				</div>
			</div>
		</Card>
	</div>
{/if}

<style>
	@keyframes slide-in-from-bottom {
		from {
			transform: translateY(100%);
			opacity: 0;
		}
		to {
			transform: translateY(0);
			opacity: 1;
		}
	}

	.animate-in {
		animation: slide-in-from-bottom 0.3s ease-out;
	}
</style>
