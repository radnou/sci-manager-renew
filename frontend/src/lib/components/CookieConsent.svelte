<script lang="ts">
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';

	const showBanner = writable(false);
	const consentGiven = writable(false);

	const CONSENT_KEY = 'gerersci_cookie_consent';

	onMount(() => {
		// Vérifier si le consentement a déjà été donné
		const savedConsent = localStorage.getItem(CONSENT_KEY);
		if (savedConsent) {
			consentGiven.set(true);
			showBanner.set(false);
		} else {
			// Afficher le banner après un court délai pour meilleure UX
			setTimeout(() => {
				showBanner.set(true);
			}, 500);
		}
	});

	function acceptAll() {
		const consent = {
			necessary: true, // Toujours true
			analytics: false, // Pas d'analytics pour l'instant
			marketing: false, // Pas de marketing
			timestamp: Date.now()
		};

		localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
		consentGiven.set(true);
		showBanner.set(false);
	}

	function acceptNecessary() {
		const consent = {
			necessary: true,
			analytics: false,
			marketing: false,
			timestamp: Date.now()
		};

		localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
		consentGiven.set(true);
		showBanner.set(false);
	}

	// Pour debug en dev: permet de réinitialiser le consentement
	if (typeof window !== 'undefined' && import.meta.env.DEV) {
		(window as any).resetCookieConsent = () => {
			localStorage.removeItem(CONSENT_KEY);
			consentGiven.set(false);
			showBanner.set(true);
			console.log('✅ Cookie consent réinitialisé. Rechargez la page.');
		};
	}
</script>

{#if $showBanner && !$consentGiven}
	<div
		class="fixed right-0 bottom-0 left-0 z-[9999] animate-in p-4 duration-300 slide-in-from-bottom sm:p-6"
		role="dialog"
		aria-live="polite"
		aria-label="Cookie consent banner"
	>
		<Card class="mx-auto max-w-4xl border-2 bg-white shadow-2xl dark:bg-slate-900">
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
							En continuant, vous acceptez l'utilisation de cookies techniques nécessaires au
							service.
							<a href="/privacy" class="ml-1 text-blue-600 hover:underline dark:text-blue-400">
								En savoir plus →
							</a>
						</p>
					</div>

					<div class="flex flex-col gap-2 sm:flex-row sm:items-center">
						<Button variant="outline" size="sm" onclick={acceptNecessary} class="whitespace-nowrap">
							Cookies essentiels uniquement
						</Button>
						<Button
							size="sm"
							onclick={acceptAll}
							class="border-0 bg-gradient-to-r from-blue-500 to-cyan-500 whitespace-nowrap text-white hover:from-blue-600 hover:to-cyan-600"
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
