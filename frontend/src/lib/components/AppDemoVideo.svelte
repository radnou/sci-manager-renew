<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	/**
	 * Each scene has sequential steps: cursor moves → click → tooltip shows → pause → next step.
	 * Only ONE thing animates at a time. Never cursor + tooltip simultaneously.
	 */

	interface Step {
		/** Where cursor moves to (% of container) */
		targetX: number;
		targetY: number;
		/** Tooltip text shown AFTER cursor arrives and clicks */
		tooltip: string;
		/** Duration cursor takes to travel (ms) */
		moveDuration: number;
		/** How long the tooltip stays visible before next step (ms) */
		readDuration: number;
	}

	interface Scene {
		imageLight: string;
		imageDark: string;
		alt: string;
		steps: Step[];
	}

	const scenes: Scene[] = [
		{
			imageLight: '/images/showcase/dashboard-light.png',
			imageDark: '/images/showcase/dashboard-dark.png',
			alt: 'Tableau de bord',
			steps: [
				{ targetX: 22, targetY: 22, tooltip: '2 SCI · 4 biens · 100% recouvrement', moveDuration: 1000, readDuration: 2000 },
				{ targetX: 72, targetY: 22, tooltip: 'Cashflow net consolidé : 64 900 €', moveDuration: 800, readDuration: 2000 }
			]
		},
		{
			imageLight: '/images/showcase/biens-grid.png',
			imageDark: '/images/showcase/biens-grid-dark.png',
			alt: 'Grille des biens',
			steps: [
				{ targetX: 22, targetY: 52, tooltip: 'Statut locatif en temps réel', moveDuration: 1000, readDuration: 2000 },
				{ targetX: 58, targetY: 62, tooltip: 'Rendement brut calculé', moveDuration: 800, readDuration: 2000 }
			]
		},
		{
			imageLight: '/images/showcase/loyers-with-button.png',
			imageDark: '/images/showcase/loyers-with-button-dark.png',
			alt: 'Suivi des loyers',
			steps: [
				{ targetX: 30, targetY: 52, tooltip: 'Loyer en retard détecté automatiquement', moveDuration: 1000, readDuration: 2000 },
				{ targetX: 72, targetY: 68, tooltip: 'Générer quittance en 1 clic', moveDuration: 900, readDuration: 2000 }
			]
		},
		{
			imageLight: '/images/showcase/finances-consolidated.png',
			imageDark: '/images/showcase/finances-consolidated-dark.png',
			alt: 'Vue financière consolidée',
			steps: [
				{ targetX: 35, targetY: 45, tooltip: 'Revenus vs charges par mois', moveDuration: 1000, readDuration: 2000 },
				{ targetX: 62, targetY: 58, tooltip: 'Cashflow net multi-SCI', moveDuration: 800, readDuration: 2000 }
			]
		},
		{
			imageLight: '/images/showcase/fiche-identite.png',
			imageDark: '/images/showcase/fiche-identite-dark.png',
			alt: 'Fiche bien détaillée',
			steps: [
				{ targetX: 28, targetY: 48, tooltip: 'DPE, surface, loyer, bail — tout en un', moveDuration: 1000, readDuration: 2000 },
				{ targetX: 55, targetY: 28, tooltip: '9 onglets de gestion complète', moveDuration: 800, readDuration: 2000 }
			]
		}
	];

	let currentScene = $state(0);
	let cursorX = $state(50);
	let cursorY = $state(50);
	let cursorMoving = $state(false);
	let showClick = $state(false);
	let activeTooltip = $state<{ text: string; x: number; y: number } | null>(null);
	let paused = $state(false);
	let destroyed = false;

	let timers: ReturnType<typeof setTimeout>[] = [];

	function clearTimers() {
		for (const t of timers) clearTimeout(t);
		timers = [];
	}

	function delay(ms: number): Promise<void> {
		return new Promise(resolve => {
			const t = setTimeout(resolve, ms);
			timers.push(t);
		});
	}

	async function playScene(sceneIndex: number) {
		if (destroyed) return;
		const scene = scenes[sceneIndex];

		// Reset state
		activeTooltip = null;
		showClick = false;

		// Start cursor at center
		cursorMoving = false;
		cursorX = 50;
		cursorY = 50;
		await delay(100);

		for (const step of scene.steps) {
			if (destroyed) return;

			// Wait if paused
			while (paused && !destroyed) {
				await delay(200);
			}
			if (destroyed) return;

			// 1. Hide any previous tooltip
			activeTooltip = null;
			await delay(200);

			// 2. Move cursor to target (CSS transition handles the animation)
			cursorMoving = true;
			cursorX = step.targetX;
			cursorY = step.targetY;

			// Wait for cursor to arrive
			await delay(step.moveDuration);
			if (destroyed) return;

			// 3. Click ripple
			showClick = true;
			await delay(400);
			showClick = false;
			await delay(200);

			// 4. Show tooltip (cursor is now still)
			activeTooltip = { text: step.tooltip, x: step.targetX, y: step.targetY };

			// 5. Hold for reading
			await delay(step.readDuration);
			if (destroyed) return;
		}

		// Hide tooltip before scene change
		activeTooltip = null;
		await delay(300);

		// Next scene
		if (!destroyed) {
			const next = (sceneIndex + 1) % scenes.length;
			currentScene = next;
			playScene(next);
		}
	}

	function goToScene(index: number) {
		clearTimers();
		currentScene = index;
		playScene(index);
	}

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

		<!-- Cursor -->
		<div
			class="pointer-events-none absolute z-10"
			class:cursor-moving={cursorMoving}
			class:cursor-instant={!cursorMoving}
			style="left: {cursorX}%; top: {cursorY}%"
		>
			<svg width="24" height="24" viewBox="0 0 24 24" class="drop-shadow-md" aria-hidden="true">
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
			<div class="pointer-events-none absolute z-20" style="left: {cursorX}%; top: {cursorY}%">
				<div class="click-ripple"></div>
			</div>
		{/if}

		<!-- Tooltip (appears AFTER cursor stops, never during movement) -->
		{#if activeTooltip}
			<div
				class="pointer-events-none absolute z-30 -translate-x-1/2 tooltip-enter"
				style="left: {activeTooltip.x}%; top: {Math.max(activeTooltip.y - 8, 4)}%"
			>
				<div
					class="whitespace-nowrap rounded-full bg-slate-900/90 px-4 py-1.5 text-xs font-medium text-white shadow-lg backdrop-blur-sm dark:bg-white/90 dark:text-slate-900"
				>
					{activeTooltip.text}
				</div>
			</div>
		{/if}
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
	.cursor-moving {
		transition:
			left 1s cubic-bezier(0.25, 0.1, 0.25, 1),
			top 1s cubic-bezier(0.25, 0.1, 0.25, 1);
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
		animation: ripple 500ms ease-out forwards;
	}

	@keyframes ripple {
		0% {
			transform: translate(-50%, -50%) scale(0);
			opacity: 1;
		}
		100% {
			transform: translate(-50%, -50%) scale(2.5);
			opacity: 0;
		}
	}

	.tooltip-enter {
		animation: tooltipIn 350ms ease-out;
	}

	@keyframes tooltipIn {
		from {
			opacity: 0;
			transform: translate(-50%, 6px);
		}
		to {
			opacity: 1;
			transform: translate(-50%, 0);
		}
	}
</style>
