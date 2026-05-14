<script lang="ts">
	import FAQSection from '$lib/landing/FAQSection.svelte';
	import { Button } from '$lib/components/ui/button';
	import { ArrowRight } from 'lucide-svelte';

	let openFaqIndex = $state<number | null>(0);
</script>

<svelte:head>
	<title>FAQ — GérerSCI</title>
	<meta
		name="description"
		content="Foire aux questions de GérerSCI : tarifs, sécurité des données, fonctionnalités, annulation, conformité fiscale et RGPD."
	/>
	<link rel="canonical" href="https://gerersci.fr/faq" />
</svelte:head>

<section class="border-b border-slate-200 bg-slate-50 py-12 dark:border-slate-800 dark:bg-slate-950">
	<div class="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
		<h1 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
			Questions fréquentes
		</h1>
		<p class="mt-4 text-base text-slate-600 dark:text-slate-400">
			Tarifs, sécurité, fonctionnalités, conformité — toutes les réponses utiles avant de vous lancer.
		</p>
	</div>
</section>

<FAQSection bind:openFaqIndex />

<section class="bg-slate-50 py-16 dark:bg-slate-950">
	<div class="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
		<h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">
			Une autre question ?
		</h2>
		<p class="mt-3 text-sm text-slate-600 dark:text-slate-400">
			Écrivez-nous à
			<a class="font-medium text-blue-600 underline hover:text-blue-700 dark:text-blue-400" href="mailto:support@gerersci.fr">
				support@gerersci.fr
			</a>
			— réponse sous 48h ouvrées.
		</p>
		<div class="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
			<Button href="/pricing" class="gap-2">
				Voir les tarifs
				<ArrowRight class="h-4 w-4" />
			</Button>
			<Button href="/register" variant="outline">Créer un compte</Button>
		</div>
	</div>
</section>
