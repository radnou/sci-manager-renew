<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	/**
	 * Animated app showcase: screenshots cycle with sequential annotation tooltips.
	 * Accepts an activeScene prop for external navigation (e.g. step cards).
	 */

	interface Annotation {
		text: string;
		x: number;
		y: number;
	}

	interface Scene {
		imageLight: string;
		imageDark: string;
		alt: string;
		label: string;
		annotations: Annotation[];
		/** Time each annotation stays visible (ms) */
		readDuration: number;
	}

	const scenes: Scene[] = [
		{
			imageLight: '/images/showcase/onboarding-step1.png',
			imageDark: '/images/showcase/onboarding-step1-dark.png',
			alt: 'Création de SCI',
			label: '① Créez votre SCI',
			annotations: [
				{ text: 'Nom, régime fiscal — 2 minutes', x: 50, y: 35 },
			],
			readDuration: 3000,
		},
		{
			imageLight: '/images/showcase/biens-grid.png',
			imageDark: '/images/showcase/biens-grid-dark.png',
			alt: 'Grille des biens',
			label: '② Ajoutez vos biens',
			annotations: [
				{ text: 'Loyer, rendement et statut locatif par bien', x: 42, y: 30 },
			],
			readDuration: 3000,
		},
		{
			imageLight: '/images/showcase/loyers-with-button.png',
			imageDark: '/images/showcase/loyers-with-button-dark.png',
			alt: 'Suivi des loyers',
			label: '② Suivi des loyers',
			annotations: [
				{ text: 'Historique et alertes impayés automatiques', x: 45, y: 35 },
			],
			readDuration: 3000,
		},
		{
			imageLight: '/images/showcase/fiche-identite.png',
			imageDark: '/images/showcase/fiche-identite-dark.png',
			alt: 'Associés et parts',
			label: '② Gouvernance',
			annotations: [
				{ text: 'Associés, parts sociales et rôles', x: 40, y: 35 },
			],
			readDuration: 3000,
		},
		{
			imageLight: '/images/showcase/finances-consolidated.png',
			imageDark: '/images/showcase/finances-consolidated-dark.png',
			alt: 'Vue financière',
			label: '③ Pilotez chaque mois',
			annotations: [
				{ text: 'Revenus, charges et cashflow consolidés', x: 50, y: 30 },
			],
			readDuration: 3000,
		},
		{
			imageLight: '/images/showcase/dashboard-light.png',
			imageDark: '/images/showcase/dashboard-dark.png',
			alt: 'Tableau de bord',
			label: '③ Tableau de bord',
			annotations: [
				{ text: 'KPIs, alertes et activité en un coup d\'oeil', x: 50, y: 32 },
			],
			readDuration: 3000,
		},
	];

	interface Props {
		activeScene?: number;
		onSceneChange?: (index: number) => void;
	}

	let { activeScene = 0, onSceneChange }: Props = $props();

	let currentScene = $state(0);
	let activeAnnotationIndex = $state(-1);
	let paused = $state(false);
	let destroyed = false;

	let timers: ReturnType<typeof setTimeout>[] = [];

	function clearTimers() {
		for (const t of timers) clearTimeout(t);
		timers = [];
	}

	function delay(ms: number): Promise<void> {
		return new Promise((resolve) => {
			const t = setTimeout(resolve, ms);
			timers.push(t);
		});
	}

	async function playScene(sceneIndex: number) {
		if (destroyed) return;
		const scene = scenes[sceneIndex];
		activeAnnotationIndex = -1;

		// Brief pause before starting annotations
		await delay(600);

		// Show each annotation one by one
		for (let i = 0; i < scene.annotations.length; i++) {
			if (destroyed) return;

			while (paused && !destroyed) {
				await delay(200);
			}
			if (destroyed) return;

			// Show this annotation
			activeAnnotationIndex = i;

			// Hold for reading
			await delay(scene.readDuration);
		}

		// Brief pause before scene change
		activeAnnotationIndex = -1;
		await delay(400);

		// Next scene
		if (!destroyed) {
			const next = (sceneIndex + 1) % scenes.length;
			currentScene = next;
			onSceneChange?.(next);
			playScene(next);
		}
	}

	function goToScene(index: number) {
		clearTimers();
		currentScene = index;
		onSceneChange?.(index);
		playScene(index);
	}

	// React to external activeScene changes
	$effect(() => {
		if (activeScene !== currentScene) {
			goToScene(activeScene);
		}
	});

	onMount(() => {
		playScene(0);
	});

	onDestroy(() => {
		destroyed = true;
		clearTimers();
	});
</script>

<div
	class="relative overflow-hidden rounded-2xl border border-slate-200 shadow-2xl dark:border-slate-700"
	onmouseenter={() => (paused = true)}
	onmouseleave={() => (paused = false)}
	role="img"
	aria-label="Démonstration de l'application GérerSCI"
>
	<!-- Browser chrome -->
	<div
		class="flex items-center gap-1.5 border-b border-slate-200 bg-slate-100 px-3 py-2 dark:border-slate-700 dark:bg-slate-800"
	>
		<div class="flex gap-1.5">
			<div class="h-2.5 w-2.5 rounded-full bg-red-400"></div>
			<div class="h-2.5 w-2.5 rounded-full bg-amber-400"></div>
			<div class="h-2.5 w-2.5 rounded-full bg-emerald-400"></div>
		</div>
		<div class="mx-auto text-xs text-slate-400 dark:text-slate-500">gerersci.fr</div>
	</div>

	<!-- Screenshots with crossfade -->
	<div class="relative aspect-[16/10]">
		{#each scenes as scene, i}
			<img
				src={scene.imageLight}
				alt={scene.alt}
				class="absolute inset-0 h-full w-full object-cover transition-opacity duration-500 dark:hidden"
				class:opacity-100={currentScene === i}
				class:opacity-0={currentScene !== i}
				width="1440"
				height="900"
				decoding="async"
			/>
			<img
				src={scene.imageDark}
				alt={scene.alt}
				class="absolute inset-0 hidden h-full w-full object-cover transition-opacity duration-500 dark:block"
				class:opacity-100={currentScene === i}
				class:opacity-0={currentScene !== i}
				width="1440"
				height="900"
				decoding="async"
			/>
		{/each}

		<!-- Annotations — one at a time, centered on target -->
		{#each scenes[currentScene]?.annotations ?? [] as ann, j}
			{#if activeAnnotationIndex === j}
				<div
					class="pointer-events-none absolute z-30 -translate-x-1/2 -translate-y-full annotation-enter"
					style="left: {ann.x}%; top: {ann.y}%"
				>
					<div
						class="relative whitespace-nowrap rounded-lg bg-slate-900/90 px-4 py-2 text-xs font-medium text-white shadow-xl backdrop-blur-sm dark:bg-white/90 dark:text-slate-900"
					>
						{ann.text}
						<!-- Arrow pointing down -->
						<div
							class="absolute left-1/2 top-full -translate-x-1/2 border-[6px] border-transparent border-t-slate-900/90 dark:border-t-white/90"
						></div>
					</div>
				</div>
				<!-- Highlight pulse on the target area -->
				<div
					class="pointer-events-none absolute z-20 -translate-x-1/2 -translate-y-1/2 highlight-pulse"
					style="left: {ann.x}%; top: {ann.y + 3}%"
				>
					<div class="h-10 w-10 rounded-full border-2 border-blue-400/60"></div>
				</div>
			{/if}
		{/each}

		<!-- Scene label -->
		<div class="absolute bottom-3 left-3 z-10">
			<span
				class="rounded-md bg-black/50 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-sm"
			>
				{scenes[currentScene]?.label}
			</span>
		</div>
	</div>
</div>

<style>
	.annotation-enter {
		animation: annotationIn 400ms ease-out;
	}

	@keyframes annotationIn {
		from {
			opacity: 0;
			transform: translate(-50%, calc(-100% + 8px));
		}
		to {
			opacity: 1;
			transform: translate(-50%, -100%);
		}
	}

	.highlight-pulse {
		animation: pulse 1.5s ease-in-out infinite;
	}

	@keyframes pulse {
		0%,
		100% {
			transform: translate(-50%, -50%) scale(1);
			opacity: 0.6;
		}
		50% {
			transform: translate(-50%, -50%) scale(1.4);
			opacity: 0;
		}
	}
</style>
