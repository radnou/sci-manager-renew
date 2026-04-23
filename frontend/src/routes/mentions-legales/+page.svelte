<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { ArrowLeft } from 'lucide-svelte';
	import { goto } from '$app/navigation';
</script>

<div class="min-h-screen bg-slate-50 py-16 dark:bg-slate-950">
	<div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
		<Button variant="outline" size="sm" class="mb-8 gap-2" onclick={() => goto('/')}>
			<ArrowLeft class="h-4 w-4" />
			Retour
		</Button>

		<h1 class="mb-8 text-3xl font-bold text-slate-900 dark:text-white">Mentions légales</h1>

		<div class="space-y-8">
			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Éditeur du site</h2>
				<p class="text-slate-600 dark:text-slate-300">
					<strong>GérerSCI</strong> — Géré par Radnoumane Mossabely
				</p>
				<p class="text-slate-600 dark:text-slate-300">
					Email : contact@gerersci.fr
				</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Hébergement</h2>
				<p class="text-slate-600 dark:text-slate-300">
					OVH Cloud — France 🇫🇷<br />
					2 rue Kellermann, 59100 Roubaix<br />
					Site : <a href="https://www.ovhcloud.com" class="text-blue-600 underline">ovhcloud.com</a>
				</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Responsable de la publication</h2>
				<p class="text-slate-600 dark:text-slate-300">Radnoumane Mossabely — contact@gerersci.fr</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">RGPD — Délégué à la protection des données</h2>
				<p class="text-slate-600 dark:text-slate-300">
					Pour toute question relative à vos données personnelles :<br />
					📧 privacy@gerersci.fr
				</p>
				<p class="text-slate-600 dark:text-slate-300">
					Vos droits : accès, rectification, effacement, portabilité, limitation, opposition.
				</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Propriété intellectuelle</h2>
				<p class="text-slate-600 dark:text-slate-300">
					Tout le contenu du site (textes, images, code) est la propriété exclusive de GérerSCI.
					Toute reproduction sans autorisation est interdite.
				</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Cookies</h2>
				<p class="text-slate-600 dark:text-slate-300">
					Ce site utilise des cookies essentiels (connexion, sécurité) et des cookies analytiques
					anonymisés (Umami). Vous pouvez modifier vos préférences à tout moment via la bannière
					cookies en bas de page.
				</p>
			</section>
		</div>

		<footer class="mt-16 border-t border-slate-200 pt-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
			© {new Date().getFullYear()} GérerSCI — Tous droits réservés
		</footer>
	</div>
</div>
