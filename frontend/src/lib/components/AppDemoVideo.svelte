<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	interface Annotation {
		text: string;
		x: number;
		y: number;
		delay: number;
	}

	interface CursorMotion {
		startX: number;
		startY: number;
		endX: number;
		endY: number;
		clickAt: number;
	}

	interface Scene {
		imageLight: string;
		imageDark: string;
		alt: string;
		annotations: Annotation[];
		cursor: CursorMotion;
		duration: number;
	}

	const scenes: Scene[] = [
		{
			imageLight: '/images/showcase/dashboard-light.png',
			imageDark: '/images/showcase/dashboard-dark.png',
			alt: 'Tableau de bord',
			annotations: [
				{ text: '2 SCI, 4 biens, 100% recouvrement', x: 30, y: 20, delay: 500 },
				{ text: 'Cashflow net consolide', x: 75, y: 20, delay: 1500 }
			],
			cursor: { startX: 50, startY: 50, endX: 30, endY: 20, clickAt: 2000 },
			duration: 4000
		},
		{
			imageLight: '/images/showcase/biens-grid.png',
			imageDark: '/images/showcase/biens-grid-dark.png',
			alt: 'Grille des biens',
			annotations: [
				{ text: 'Statut locatif en temps reel', x: 25, y: 45, delay: 500 },
				{ text: 'Rendement brut calcule', x: 60, y: 55, delay: 1500 }
			],
			cursor: { startX: 80, startY: 30, endX: 25, endY: 45, clickAt: 2000 },
			duration: 4000
		},
		{
			imageLight: '/images/showcase/loyers-with-button.png',
			imageDark: '/images/showcase/loyers-with-button-dark.png',
			alt: 'Suivi des loyers',
			annotations: [
				{ text: 'Loyer en retard detecte', x: 40, y: 50, delay: 500 },
				{ text: 'Generer quittance en 1 clic', x: 70, y: 60, delay: 1800 }
			],
			cursor: { startX: 50, startY: 30, endX: 70, endY: 60, clickAt: 2500 },
			duration: 4000
		},
		{
			imageLight: '/images/showcase/finances-consolidated.png',
			imageDark: '/images/showcase/finances-consolidated-dark.png',
			alt: 'Vue financiere',
			annotations: [
				{ text: 'Revenus vs charges par mois', x: 35, y: 40, delay: 500 },
				{ text: 'Cashflow net multi-SCI', x: 65, y: 55, delay: 1500 }
			],
			cursor: { startX: 20, startY: 60, endX: 65, endY: 55, clickAt: 2000 },
			duration: 4000
		},
		{
			imageLight: '/images/showcase/fiche-identite.png',
			imageDark: '/images/showcase/fiche-identite-dark.png',
			alt: 'Fiche bien detaillee',
			annotations: [
				{ text: 'DPE, surface, loyer, bail', x: 30, y: 45, delay: 500 },
				{ text: '9 onglets de gestion', x: 60, y: 30, delay: 1500 }
			],
			cursor: { startX: 50, startY: 70, endX: 60, endY: 30, clickAt: 2000 },
			duration: 4000
		}
	];

	let currentScene = $state(0);
	let cursorX = $state(50);
	let cursorY = $state(50);
	let showClick = $state(false);
	let visibleAnnotations = $state<number[]>([]);
	let paused = $state(false);

	let sceneTimer: ReturnType<typeof setTimeout> | undefined;
	let pendingTimers: ReturnType<typeof setTimeout>[] = [];

	function clearAllTimers() {
		if (sceneTimer) clearTimeout(sceneTimer);
		for (const t of pendingTimers) clearTimeout(t);
		pendingTimers = [];
	}

	function scheduleTimer(fn: () => void, delay: number) {
		const t = setTimeout(fn, delay);
		pendingTimers.push(t);
		return t;
	}

	function startScene(index: number) {
		clearAllTimers();
		const scene = scenes[index];
		visibleAnnotations = [];
		showClick = false;

		// Set initial cursor position instantly
		cursorX = scene.cursor.startX;
		cursorY = scene.cursor.startY;

		// Start cursor movement after brief delay
		scheduleTimer(() => {
			if (paused) return;
			cursorX = scene.cursor.endX;
			cursorY = scene.cursor.endY;
		}, 200);

		// Show annotations with staggered delays
		scene.annotations.forEach((_, j) => {
			scheduleTimer(() => {
				if (paused) return;
				visibleAnnotations = [...visibleAnnotations, j];
			}, scene.annotations[j].delay);
		});

		// Click ripple effect
		scheduleTimer(() => {
			if (paused) return;
			showClick = true;
			scheduleTimer(() => {
				showClick = false;
			}, 600);
		}, scene.cursor.clickAt);

		// Advance to next scene
		sceneTimer = setTimeout(() => {
			if (paused) {
				sceneTimer = setTimeout(() => advanceScene(index), 500);
				return;
			}
			advanceScene(index);
		}, scene.duration);
	}

	function advanceScene(fromIndex: number) {
		const next = (fromIndex + 1) % scenes.length;
		currentScene = next;
		startScene(next);
	}

	function goToScene(index: number) {
		currentScene = index;
		startScene(index);
	}

	onMount(() => {
		startScene(0);
	});

	onDestroy(() => {
		clearAllTimers();
	});
</script>

<div
	class="relative overflow-hidden rounded-2xl border border-slate-200 shadow-2xl dark:border-slate-700"
	onmouseenter={() => (paused = true)}
	onmouseleave={() => {
		paused = false;
	}}
	role="img"
	aria-label="Demonstration de l'application GererSCI"
>
	<!-- Browser chrome bar -->
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

	<!-- Screenshot area with crossfade -->
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

		<!-- Fake cursor -->
		<div
			class="pointer-events-none absolute z-10 transition-all duration-[1500ms] ease-in-out"
			style="left: {cursorX}%; top: {cursorY}%"
		>
			<svg
				width="20"
				height="20"
				viewBox="0 0 24 24"
				class="drop-shadow-lg"
				aria-hidden="true"
			>
				<path d="M5 3l14 8-6 2-4 6z" fill="white" stroke="black" stroke-width="1" />
			</svg>
		</div>

		<!-- Click ripple -->
		{#if showClick}
			<div
				class="pointer-events-none absolute z-20"
				style="left: {cursorX}%; top: {cursorY}%"
			>
				<div class="click-ripple"></div>
			</div>
		{/if}

		<!-- Annotations -->
		{#each scenes[currentScene]?.annotations ?? [] as ann, j}
			{#if visibleAnnotations.includes(j)}
				<div
					class="pointer-events-none absolute z-10 annotation-pill"
					style="left: {ann.x}%; top: {ann.y}%"
				>
					<div
						class="whitespace-nowrap rounded-full bg-slate-900/90 px-3 py-1 text-xs font-medium text-white shadow-lg dark:bg-white/90 dark:text-slate-900"
					>
						{ann.text}
					</div>
				</div>
			{/if}
		{/each}
	</div>

	<!-- Progress dots -->
	<div class="flex justify-center gap-1.5 bg-slate-50 py-2 dark:bg-slate-900">
		{#each scenes as _, i}
			<button
				class="h-1.5 rounded-full transition-all duration-300 {currentScene === i
					? 'w-6 bg-blue-500'
					: 'w-1.5 bg-slate-300 dark:bg-slate-600'}"
				onclick={() => goToScene(i)}
				aria-label="Scene {i + 1}"
			></button>
		{/each}
	</div>
</div>

<style>
	.click-ripple {
		width: 2rem;
		height: 2rem;
		border-radius: 9999px;
		background: rgba(59, 130, 246, 0.3);
		transform: translate(-50%, -50%) scale(0);
		animation: ripple 600ms ease-out forwards;
	}

	@keyframes ripple {
		0% {
			transform: translate(-50%, -50%) scale(0);
			opacity: 1;
		}
		100% {
			transform: translate(-50%, -50%) scale(3);
			opacity: 0;
		}
	}

	.annotation-pill {
		animation: annotationIn 300ms ease-out;
	}

	@keyframes annotationIn {
		from {
			opacity: 0;
			transform: translateY(4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
