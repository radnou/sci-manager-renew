<script lang="ts">
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';
	import { grantMatomoConsent, revokeMatomoConsent } from '$lib/matomo';

	const showBanner = writable(false);
	const consentGiven = writable(false);

	const CONSENT_KEY = 'gerersci_cookie_consent';

	onMount(() => {
		// Vérifier si le consentement a déjà été donné
		const savedConsent = localStorage.getItem(CONSENT_KEY);
		if (savedConsent) {
			consentGiven.set(true);
			showBanner.set(false);
			// Restore Matomo consent if analytics was accepted
			try {
				const parsed = JSON.parse(savedConsent);
				if (parsed.analytics) {
					grantMatomoConsent();
				}
			} catch {
				// ignore parse errors
			}
		} else {
			// Afficher le banner après un court délai pour meilleure UX
			setTimeout(() => {
				showBanner.set(true);
			}, 500);
		}
	});

	function acceptAll() {
		const consent = {
			necessary: true,
			analytics: true,
			marketing: false,
			timestamp: Date.now()
		};

		localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
		consentGiven.set(true);
		showBanner.set(false);
		grantMatomoConsent();
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
		revokeMatomoConsent();
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
		class="fixed bottom-0 left-0 right-0 z-[9999] p-4 sm:p-6 animate-in slide-in-from-bottom duration-300"
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
							Nous utilisons des <strong>cookies essentiels</strong> pour l'authentification et le
							fonctionnement du service, ainsi que des <strong>cookies d'analyse</strong> (Matomo,
							auto-hébergé en France) pour améliorer votre expérience. Aucun tracking publicitaire.
						</p>
						<p class="text-xs text-slate-500 dark:text-slate-500">
							Vos données d'analyse restent sur nos serveurs en France et ne sont jamais partagées.
							<a href="/confidentialite" class="text-blue-600 dark:text-blue-400 hover:underline ml-1">
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
