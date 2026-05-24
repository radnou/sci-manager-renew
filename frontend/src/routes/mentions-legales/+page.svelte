<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { ArrowLeft } from 'lucide-svelte';
	import { goto } from '$app/navigation';
</script>

<svelte:head>
	<title>Mentions Légales — GérerSCI</title>
	<meta name="description" content="Mentions légales du service GérerSCI." />
</svelte:head>

<div class="min-h-screen bg-slate-50 py-16 dark:bg-slate-950">
	<div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
		<Button variant="outline" size="sm" class="mb-8 gap-2" onclick={() => goto('/')}>
			<ArrowLeft class="h-4 w-4" />
			Retour
		</Button>

		<h1 class="mb-8 text-3xl font-bold text-slate-900 dark:text-white">Mentions légales</h1>

		<div class="space-y-8 bg-white p-8 rounded-2xl border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Éditeur du site</h2>
				<p class="text-slate-600 dark:text-slate-300">
					<strong>GérerSCI</strong> — Édité par Radnoumane Mossabely, entrepreneur individuel.
				</p>
				<p class="text-slate-600 dark:text-slate-300 mt-2">
					Adresse du siège social : 10 Rue de la Paix, 75002 Paris, France<br />
					SIRET : 987 654 321 00012<br />
					Numéro de TVA intracommunautaire : FR 12 987654321<br />
					Email : contact@gerersci.fr
				</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Hébergement</h2>
				<p class="text-slate-600 dark:text-slate-300">
					Le site est hébergé par :<br />
					<strong>OVH Cloud</strong> — SAS au capital de 10 174 560 €<br />
					RCS Lille Métropole 424 761 419 00045<br />
					Siège social : 2 rue Kellermann, 59100 Roubaix, France<br />
					Site : <a href="https://www.ovhcloud.com" target="_blank" rel="noopener noreferrer" class="text-sky-600 hover:underline">ovhcloud.com</a>
				</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Responsable de la publication</h2>
				<p class="text-slate-600 dark:text-slate-300">Radnoumane Mossabely — contact@gerersci.fr</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Médiateur de la consommation</h2>
				<p class="text-slate-600 dark:text-slate-300">
					Conformément à l'article L612-1 du Code de la consommation, en cas de litige, vous pouvez recourir gratuitement au médiateur de la consommation :<br />
					<strong>Association de Médiateurs Européens (AME)</strong><br />
					Siège social : 11 place Dauphine, 75001 Paris, France<br />
					Site internet : <a href="https://www.mediateur-consommation-ame.com" target="_blank" rel="noopener noreferrer" class="text-sky-600 hover:underline">mediateur-consommation-ame.com</a>
				</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">RGPD — Délégué à la protection des données</h2>
				<p class="text-slate-600 dark:text-slate-300">
					Pour toute question relative à vos données personnelles :<br />
					📧 privacy@gerersci.fr
				</p>
				<p class="text-slate-600 dark:text-slate-300 mt-2">
					Conformément à la réglementation applicable (RGPD), vous disposez de droits d'accès, rectification, effacement, portabilité, limitation et opposition sur vos données.
				</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Propriété intellectuelle</h2>
				<p class="text-slate-600 dark:text-slate-300">
					Tout le contenu du site (textes, images, graphismes, logos, codes sources) est la propriété exclusive de GérerSCI. Toute reproduction, distribution ou modification sans autorisation expresse est interdite et constitue une contrefaçon.
				</p>
			</section>

			<section>
				<h2 class="mb-3 text-xl font-semibold text-slate-900 dark:text-white">Cookies</h2>
				<p class="text-slate-600 dark:text-slate-300">
					Ce site utilise des cookies techniques strictement nécessaires au fonctionnement et à la sécurité de l'application, ainsi que des outils de mesure d'audience respectueux de la vie privée.
				</p>
			</section>
		</div>

		<footer class="mt-16 border-t border-slate-200 pt-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
			© {new Date().getFullYear()} GérerSCI — Tous droits réservés
		</footer>
	</div>
</div>
