<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { ArrowRight, ChevronDown } from '@lucide/svelte';
	import { supabase } from '$lib/supabase';

	let isLoggedIn = $state(false);

	$effect(() => {
		supabase.auth.getSession().then(({ data }) => {
			isLoggedIn = !!data.session;
		});
	});

	function scrollToSection(id: string) {
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
	}
</script>

<section class="relative overflow-hidden bg-white py-20 sm:py-32 dark:bg-slate-900">
	<div
		class="pointer-events-none absolute inset-0 bg-gradient-to-br from-blue-50/80 via-transparent to-cyan-50/60 dark:from-blue-950/30 dark:to-cyan-950/20"
	></div>
	<div class="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="mx-auto max-w-3xl text-center">
			<Badge variant="secondary" class="mb-6 px-3 py-1 text-sm font-medium">
				Gérez votre SCI en toute simplicité
			</Badge>
			<h1
				class="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl md:text-6xl dark:text-white"
			>
				Gérez votre
				<span class="text-blue-600 dark:text-blue-400">SCI</span>
				comme un pro.
				<span class="block text-3xl sm:text-4xl md:text-5xl text-slate-500 font-normal mt-2">Votre SCI sous contrôle.</span>
			</h1>
			<p class="mx-auto mt-6 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
				Suivi des loyers, quittances automatiques, déclarations fiscales, gestion des associés
				— tout en un.
			</p>
			<div class="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
				{#if isLoggedIn}
					<Button size="lg" href="/dashboard" class="gap-2">
						Mon tableau de bord
						<ArrowRight class="h-4 w-4" />
					</Button>
				{:else}
					<Button size="lg" href="/pricing" class="gap-2">
						Démarrer maintenant
						<ArrowRight class="h-4 w-4" />
					</Button>
					<Button variant="outline" size="lg" href="#pricing" class="gap-2" aria-label="Comparer les plans de tarification">
						Comparer les plans
					</Button>
				{/if}
			</div>
		</div>
		<div class="mt-16 flex justify-center">
			<button onclick={() => scrollToSection('comment-ca-marche')} class="animate-bounce" aria-label="Descendre à la section démo">
				<ChevronDown class="h-8 w-8 text-slate-400" />
			</button>
		</div>
	</div>
</section>
