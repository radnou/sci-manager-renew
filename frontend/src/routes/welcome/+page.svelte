<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { seedDemo } from '$lib/api';
	import { trackEvent, EVENTS } from '$lib/analytics';

	let currentStep = $state(0);
	let factIndex = $state(0);
	let progress = $state(0);
	let error = $state('');

	const steps = [
		{ text: 'Création de votre espace de gestion', duration: 1500 },
		{ text: 'Chargement des données de démonstration', duration: 2000 },
		{ text: 'Calcul de vos indicateurs financiers', duration: 2000 },
		{ text: 'Préparation de votre tableau de bord', duration: 1500 },
	];

	const facts = [
		'Un loyer impayé non détecté coûte en moyenne 800€ au propriétaire.',
		'Les gestionnaires digitalisés réduisent leurs impayés de 63%.',
		'GérerSCI pré-remplit votre CERFA 2044 automatiquement.',
		'72% des gestionnaires constatent une amélioration en 12 mois.',
	];

	const totalDuration = steps.reduce((s, step) => s + step.duration, 0);

	onMount(() => {
		trackEvent(EVENTS.DEMO_SEED_START);
		// Launch API call immediately (runs in background)
		const seedPromise = seedDemo().catch((err) => {
			console.error('Demo seed failed:', err);
			error = err?.message || 'Erreur lors du chargement des données.';
		});

		// Animate steps on fixed timer (independent of API)
		let elapsed = 0;
		for (let i = 0; i < steps.length; i++) {
			setTimeout(() => { currentStep = i + 1; }, elapsed);
			elapsed += steps[i].duration;
		}

		// Progress bar animation
		const interval = setInterval(() => {
			progress = Math.min(progress + 1.5, 100);
		}, totalDuration / 67);

		// Rotate facts
		const factTimer = setInterval(() => {
			factIndex = (factIndex + 1) % facts.length;
		}, 2500);

		// Redirect after animation completes (wait for API too)
		setTimeout(async () => {
			clearInterval(interval);
			clearInterval(factTimer);
			progress = 100;
			await seedPromise;
			trackEvent(EVENTS.DEMO_SEED_COMPLETE);
			// Small delay for 100% to render
			setTimeout(() => {
				goto('/dashboard', { replaceState: true });
			}, 300);
		}, totalDuration);
	});
</script>

<svelte:head><title>Bienvenue | GérerSCI</title></svelte:head>

<div class="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
	<div class="w-full max-w-md px-6 text-center">
		<!-- Logo -->
		<h1 class="mb-2 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
			GérerSCI
		</h1>
		<p class="mb-8 text-sm text-slate-600 dark:text-slate-400">
			Bienvenue ! Nous préparons votre espace.
		</p>

		<!-- Steps -->
		<div class="mb-8 space-y-3 text-left">
			{#each steps as step, i}
				<div class="flex items-center gap-3 text-sm transition-opacity duration-300 {i < currentStep ? 'opacity-100' : i === currentStep ? 'opacity-70' : 'opacity-30'}">
					{#if i < currentStep}
						<span class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-white text-xs">✓</span>
					{:else if i === currentStep}
						<span class="flex h-6 w-6 items-center justify-center">
							<span class="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600 dark:border-slate-700 dark:border-t-blue-400"></span>
						</span>
					{:else}
						<span class="flex h-6 w-6 items-center justify-center rounded-full bg-slate-200 text-slate-400 text-xs dark:bg-slate-800 dark:text-slate-600">
							{i + 1}
						</span>
					{/if}
					<span class="text-slate-700 dark:text-slate-300 {i < currentStep ? 'text-emerald-700 dark:text-emerald-400' : ''}">
						{step.text}
					</span>
				</div>
			{/each}
		</div>

		<!-- Progress bar -->
		<div class="mb-6 h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
			<div
				class="h-full rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 transition-all duration-200"
				style="width: {progress}%"
			></div>
		</div>

		<!-- Rotating facts -->
		<div class="min-h-[3rem] text-sm text-slate-500 dark:text-slate-400" style="animation: fadeIn 0.3s ease-out">
			<p>{facts[factIndex]}</p>
		</div>

		{#if error}
			<p class="mt-4 text-xs text-rose-500">{error}</p>
		{/if}
	</div>
</div>

<style>
	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
