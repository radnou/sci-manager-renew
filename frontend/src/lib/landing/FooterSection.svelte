<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { ArrowRight } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import { trackEvent, EVENTS } from '$lib/analytics';
</script>

<footer class="border-t border-slate-200 bg-slate-50 py-16 dark:border-slate-800 dark:bg-slate-950">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="grid gap-12 md:grid-cols-4">
			<div class="col-span-2">
				<h3 class="text-lg font-bold text-slate-900 dark:text-white">GérerSCI</h3>
				<p class="mt-4 max-w-sm text-sm text-slate-600 dark:text-slate-400">
					Gérez votre SCI en 10 minutes par mois. Suivi des loyers, quittances, fiscalité — tout en un.
				</p>
				<div class="mt-6">
					<Button
						size="sm"
						class="gap-2"
						onclick={() => { trackEvent(EVENTS.LANDING_CTA_CLICK, { cta: 'footer_demarrer' }); goto('/register'); }}
					>
						Démarrer
						<ArrowRight class="h-4 w-4" />
					</Button>
				</div>
			</div>

			<div>
				<h4 class="font-semibold text-slate-900 dark:text-white">Produit</h4>
				<ul class="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-400">
					<li><a href="#features" class="hover:text-slate-900 dark:hover:text-slate-200">Fonctionnalités</a></li>
					<li><a href="#pricing" class="hover:text-slate-900 dark:hover:text-slate-200">Tarifs</a></li>
					<li><a href="/simulateur-cerfa" class="hover:text-slate-900 dark:hover:text-slate-200">Simulateur</a></li>
				</ul>
			</div>

			<div>
				<h4 class="font-semibold text-slate-900 dark:text-white">Ressources</h4>
				<ul class="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-400">
					<li><a href="/faq" class="hover:text-slate-900 dark:hover:text-slate-200">FAQ</a></li>
					<li><a href="/mentions-legales" class="hover:text-slate-900 dark:hover:text-slate-200">Mentions légales</a></li>
					<li><a href="/rgpd" class="hover:text-slate-900 dark:hover:text-slate-200">RGPD</a></li>
				</ul>
			</div>
		</div>

		<div class="mt-12 border-t border-slate-200 pt-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
			© {new Date().getFullYear()} GérerSCI — Tous droits réservés — Hébergé en France 🇫🇷
		</div>
	</div>
</footer>
