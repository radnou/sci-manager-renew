<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import AppDemoVideo from '$lib/components/AppDemoVideo.svelte';
	import { trackEvent, EVENTS } from '$lib/analytics';

	let { demoScene = $bindable(0) }: { demoScene?: number } = $props();

	const steps = [
		{ step: '①', title: 'Créez votre SCI', time: '2 minutes', desc: "Nom, régime fiscal, c'est tout.", sceneStart: 0, sceneEnd: 0 },
		{ step: '②', title: 'Ajoutez vos biens', time: '5 minutes', desc: 'Biens, loyers, associés — on vous guide.', sceneStart: 1, sceneEnd: 3 },
		{ step: '③', title: 'Pilotez chaque mois', time: '10 min/mois', desc: 'Finances, KPIs, alertes — automatisé.', sceneStart: 4, sceneEnd: 5 }
	];
</script>

<section id="comment-ca-marche" class="bg-white py-20 dark:bg-slate-900">
	<div class="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
		<div class="mb-12 text-center">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Simple</Badge>
			<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
				Comment ça marche — en 3 étapes
			</h2>
		</div>

		<!-- Demo video -->
		<div class="mx-auto max-w-5xl">
			<AppDemoVideo activeScene={demoScene} onSceneChange={(i) => { demoScene = i; }} />
		</div>

		<!-- Step navigation cards -->
		<div class="mt-8 grid gap-4 md:grid-cols-3">
			{#each steps as card, i}
				{@const isActive = demoScene >= card.sceneStart && demoScene <= card.sceneEnd}
				<button
					class="rounded-xl border p-4 text-left transition-all duration-200 {isActive
						? 'border-blue-500 bg-blue-50 shadow-md dark:border-blue-400 dark:bg-blue-950/30'
						: 'border-slate-200 bg-slate-50 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600'}"
					onclick={() => { demoScene = card.sceneStart; trackEvent(EVENTS.LANDING_STEP_MODAL_OPEN, { step: i + 1 }); }}
				>
					<div class="mb-2 flex items-center justify-between">
						<span class="text-2xl font-bold text-blue-600 dark:text-blue-400">{card.step}</span>
						<span class="text-xs text-slate-500 dark:text-slate-400">{card.time}</span>
					</div>
					<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">{card.title}</h3>
					<p class="mt-1 text-sm text-slate-600 dark:text-slate-300">{card.desc}</p>
				</button>
			{/each}
		</div>
	</div>
</section>
