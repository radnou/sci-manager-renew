<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { ArrowRight } from '@lucide/svelte';
	import { goto } from '$app/navigation';
</script>

<section class="bg-slate-900 py-20 dark:bg-slate-950">
	<div class="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
		<h2 class="text-3xl font-bold tracking-tight text-white sm:text-4xl">
			Prêt à simplifier la gestion de votre SCI ?
		</h2>
		<p class="mx-auto mt-4 max-w-2xl text-lg text-slate-300">
			Rejoignez des centaines de propriétaires qui gagnent du temps chaque mois.
		</p>
		<div class="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
			<Button size="lg" onclick={() => goto('/login')} class="gap-2">
				Créer un compte gratuit
				<ArrowRight class="h-4 w-4" />
			</Button>
			<p class="text-sm text-slate-400">Pas de carte bancaire requise.</p>
		</div>
	</div>
</section>
