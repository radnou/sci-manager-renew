<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	interface Annotation {
		text: string;
		x: number;
		y: number;
		delay: number;
	}

	interface Scene {
		imageLight: string;
		imageDark: string;
		alt: string;
		annotations: Annotation[];
		// Cursor path: array of {x, y} waypoints for smooth multi-step movement
		cursorPath: { x: number; y: number }[];
		clickAt: number; // ms when click ripple fires
		duration: number;
	}

	const scenes: Scene[] = [
		{
			imageLight: '/images/showcase/dashboard-light.png',
			imageDark: '/images/showcase/dashboard-dark.png',
			alt: 'Tableau de bord',
			annotations: [
				{ text: '2 SCI · 4 biens · 100% recouvrement', x: 25, y: 15, delay: 600 },
				{ text: 'Cashflow net consolidé : 64 900 €', x: 70, y: 15, delay: 1800 }
			],
			cursorPath: [
				{ x: 50, y: 60 },
				{ x: 35, y: 35 },
				{ x: 25, y: 18 }
			],
			clickAt: 2200,
			duration: 4500
		},
		{
			imageLight: '/images/showcase/biens-grid.png',
			imageDark: '/images/showcase/biens-grid-dark.png',
			alt: 'Grille des biens',
			annotations: [
				{ text: 'Statut locatif en temps réel', x: 20, y: 55, delay: 600 },
				{ text: 'Rendement brut calculé automatiquement', x: 55, y: 65, delay: 1800 }
			],
			cursorPath: [
				{ x: 75, y: 25 },
				{ x: 45, y: 45 },
				{ x: 25, y: 58 }
			],
			clickAt: 2200,
			duration: 4500
		},
		{
			imageLight: '/images/showcase/loyers-with-button.png',
			imageDark: '/images/showcase/loyers-with-button-dark.png',
			alt: 'Suivi des loyers',
			annotations: [
				{ text: 'Loyer en retard détecté', x: 30, y: 50, delay: 600 },
				{ text: 'Générer quittance en 1 clic', x: 65, y: 70, delay: 1800 }
			],
			cursorPath: [
				{ x: 50, y: 25 },
				{ x: 35, y: 48 },
				{ x: 68, y: 72 }
			],
			clickAt: 2800,
			duration: 4500
		},
		{
			imageLight: '/images/showcase/finances-consolidated.png',
			imageDark: '/images/showcase/finances-consolidated-dark.png',
			alt: 'Vue financière',
			annotations: [
				{ text: 'Revenus vs charges par mois', x: 30, y: 45, delay: 600 },
				{ text: 'Cashflow net multi-SCI', x: 60, y: 60, delay: 1800 }
			],
			cursorPath: [
				{ x: 20, y: 30 },
				{ x: 40, y: 50 },
				{ x: 62, y: 62 }
			],
			clickAt: 2200,
			duration: 4500
		},
		{
			imageLight: '/images/showcase/fiche-identite.png',
			imageDark: '/images/showcase/fiche-identite-dark.png',
			alt: 'Fiche bien détaillée',
			annotations: [
				{ text: 'DPE, surface, loyer, bail', x: 25, y: 50, delay: 600 },
				{ text: '9 onglets de gestion complète', x: 55, y: 25, delay: 1800 }
			],
			cursorPath: [
				{ x: 50, y: 75 },
				{ x: 30, y: 52 },
				{ x: 58, y: 28 }
			],
			clickAt: 2500,
			duration: 4500
		}
	];

	let currentScene = $state(0);
	let cursorX = $state(50);
	let cursorY = $state(50);
	let cursorAnimating = $state(false); // controls whether CSS transition is active
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

	function schedule(fn: () => void, delay: number) {
		const t = setTimeout(fn, delay);
		pendingTimers.push(t);
		return t;
	}

	function startScene(index: number) {
		clearAllTimers();
		const scene = scenes[index];
		visibleAnnotations = [];
		showClick = false;

		// 1. Instantly teleport cursor to first waypoint (no transition)
		cursorAnimating = false;
		cursorX = scene.cursorPath[0].x;
		cursorY = scene.cursorPath[0].y;

		// 2. After a frame, enable transition and animate through waypoints
		schedule(() => {
			cursorAnimating = true;
		}, 50);

		// Animate cursor along waypoints with staggered timing
		const waypointInterval = 1200; // ms between waypoints
		for (let w = 1; w < scene.cursorPath.length; w++) {
			schedule(() => {
				if (paused) return;
				cursorX = scene.cursorPath[w].x;
				cursorY = scene.cursorPath[w].y;
			}, 100 + w * waypointInterval);
		}

		// Show annotations with staggered delays
		scene.annotations.forEach((ann, j) => {
			schedule(() => {
				if (paused) return;
				visibleAnnotations = [...visibleAnnotations, j];
			}, ann.delay);
		});

		// Click ripple at cursor's current position
		schedule(() => {
			if (paused) return;
			showClick = true;
			schedule(() => {
				showClick = false;
			}, 600);
		}, scene.clickAt);

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
	onmouseleave={() => (paused = false)}
	role="img"
	aria-label="Démonstration de l'application GérerSCI"
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
			class="pointer-events-none absolute z-10"
			class:cursor-animate={cursorAnimating}
			class:cursor-instant={!cursorAnimating}
			style="left: {cursorX}%; top: {cursorY}%"
		>
			<svg
				width="24"
				height="24"
				viewBox="0 0 24 24"
				class="drop-shadow-md -translate-x-[2px] -translate-y-[2px]"
				aria-hidden="true"
			>
				<path
					d="M5.65 3.15l13.7 7.7-5.95 2.05L9.35 19l-3.7-15.85z"
					fill="white"
					stroke="#1e293b"
					stroke-width="1.2"
					stroke-linejoin="round"
				/>
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
					class="pointer-events-none absolute z-10 annotation-pill -translate-x-1/2"
					style="left: {ann.x}%; top: {ann.y}%"
				>
					<div
						class="whitespace-nowrap rounded-full bg-slate-900/90 px-3 py-1.5 text-xs font-medium text-white shadow-lg backdrop-blur-sm dark:bg-white/90 dark:text-slate-900"
					>
						{ann.text}
					</div>
				</div>
			{/if}
		{/each}
	</div>

	<!-- Progress dots -->
	<div class="flex justify-center gap-1.5 bg-slate-50 py-2.5 dark:bg-slate-900">
		{#each scenes as _, i}
			<button
				class="h-1.5 rounded-full transition-all duration-300 {currentScene === i
					? 'w-6 bg-blue-500'
					: 'w-1.5 bg-slate-300 hover:bg-slate-400 dark:bg-slate-600 dark:hover:bg-slate-500'}"
				onclick={() => goToScene(i)}
				aria-label="Scène {i + 1}"
			></button>
		{/each}
	</div>
</div>

<style>
	/* Cursor transitions: smooth when animating, instant when teleporting */
	.cursor-animate {
		transition:
			left 1s cubic-bezier(0.4, 0, 0.2, 1),
			top 1s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.cursor-instant {
		transition: none;
	}

	.click-ripple {
		width: 2rem;
		height: 2rem;
		border-radius: 9999px;
		background: rgba(59, 130, 246, 0.35);
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
		animation: annotationIn 400ms ease-out;
	}

	@keyframes annotationIn {
		from {
			opacity: 0;
			transform: translate(-50%, 8px);
		}
		to {
			opacity: 1;
			transform: translate(-50%, 0);
		}
	}
</style>
