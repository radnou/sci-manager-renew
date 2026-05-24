<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card } from '$lib/components/ui/card';
	import { onMount } from 'svelte';
	import {
		grantAnalyticsConsent,
		revokeAnalyticsConsent
	} from '$lib/analytics';

	let visible = $state(false);

	onMount(() => {
		const consent = localStorage.getItem('gerersci_cookie_consent');
		if (consent) {
			if (consent === 'all') {
				initUmami();
				grantAnalyticsConsent();
			} else if (consent === 'essential') {
				revokeAnalyticsConsent();
			} else {
				try {
					const parsed = JSON.parse(consent);
					if (parsed.analytics) {
						initUmami();
						grantAnalyticsConsent();
					} else {
						revokeAnalyticsConsent();
					}
				} catch {
					// Fallback for custom string flags
					revokeAnalyticsConsent();
				}
			}
			visible = false;
		} else {
			visible = true;
		}
	});

	function initUmami() {
		if (typeof window === 'undefined') return;
		if (document.querySelector('script[src*="analytics.gerersci.fr/script.js"]')) return;
		const script = document.createElement('script');
		script.defer = true;
		script.src = 'https://analytics.gerersci.fr/script.js';
		script.setAttribute('data-website-id', '0782cbe1-3b70-4c15-8a16-bf7b071fadf1');
		document.head.appendChild(script);
	}

	function acceptAll() {
		const consent = {
			necessary: true,
			analytics: true,
			timestamp: Date.now()
		};
		localStorage.setItem('gerersci_cookie_consent', JSON.stringify(consent));
		visible = false;
		initUmami();
		grantAnalyticsConsent();
	}

	function acceptEssential() {
		const consent = {
			necessary: true,
			analytics: false,
			timestamp: Date.now()
		};
		localStorage.setItem('gerersci_cookie_consent', JSON.stringify(consent));
		visible = false;
		revokeAnalyticsConsent();
	}
</script>

{#if visible}
	<div
		class="fixed bottom-0 left-0 right-0 z-[9999] p-4 sm:p-6 animate-in slide-in-from-bottom duration-300"
		role="dialog"
		aria-live="polite"
		aria-label="Bannière de consentement des cookies"
	>
		<Card class="mx-auto max-w-4xl border-2 shadow-2xl bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
			<div class="p-4 sm:p-6">
				<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
					<div class="flex-1 space-y-2">
						<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
							🍪 Gestion des cookies
						</h2>
						<p class="text-sm text-slate-600 dark:text-slate-400">
							Nous utilisons des <strong>cookies essentiels</strong> pour l'authentification et le
							fonctionnement du service, ainsi que des <strong>statistiques d'usage anonymes</strong> (Umami)
							pour améliorer votre expérience. Aucun tracking publicitaire, aucun partage de données.
						</p>
						<p class="text-xs text-slate-500 dark:text-slate-500">
							Nous ne revendons aucune donnée et n'utilisons aucun pixel publicitaire.
							<a href="/confidentialite" class="text-blue-600 dark:text-blue-400 hover:underline ml-1">
								En savoir plus →
							</a>
						</p>
					</div>

					<div class="flex flex-col gap-2 sm:flex-row sm:items-center">
						<Button
							variant="outline"
							size="sm"
							onclick={acceptEssential}
							class="whitespace-nowrap focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
						>
							Cookies essentiels uniquement
						</Button>
						<Button
							size="sm"
							onclick={acceptAll}
							class="whitespace-nowrap bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white border-0 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
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
