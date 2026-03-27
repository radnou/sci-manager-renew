<script lang="ts">
	import { onMount } from 'svelte';
	import { Check, Target, FileText } from 'lucide-svelte';

	type CelebrationType = 'checkmark' | 'badge' | 'confetti';

	let {
		type,
		title,
		subtitle,
		duration = 3000,
		onDismiss
	}: {
		type: CelebrationType;
		title: string;
		subtitle: string;
		duration?: number;
		onDismiss?: () => void;
	} = $props();

	let visible = $state(true);

	const confettiColors = ['#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#8b5cf6'];

	const particles = Array.from({ length: 15 }, (_, i) => ({
		id: i,
		color: confettiColors[i % confettiColors.length],
		left: Math.random() * 100,
		delay: Math.random() * 0.8,
		size: 6 + Math.random() * 6
	}));

	function dismiss() {
		visible = false;
		onDismiss?.();
	}

	onMount(() => {
		const timer = setTimeout(dismiss, duration);
		return () => clearTimeout(timer);
	});
</script>

{#if visible}
	<!-- svelte-ignore a11y_autofocus -->
	<button
		class="fixed inset-0 z-50 flex items-center justify-center animate-fadeIn"
		onclick={dismiss}
		aria-label="Fermer la notification"
		autofocus
	>
		<!-- Backdrop -->
		<div class="absolute inset-0 bg-black/10"></div>

		<!-- Confetti particles -->
		{#if type === 'confetti'}
			{#each particles as particle (particle.id)}
				<span
					class="absolute top-0 rounded-full animate-confettiFall pointer-events-none"
					style="
						left: {particle.left}%;
						width: {particle.size}px;
						height: {particle.size}px;
						background-color: {particle.color};
						animation-delay: {particle.delay}s;
					"
				></span>
			{/each}
		{/if}

		<!-- Content card -->
		<div
			class="relative max-w-sm w-full mx-4 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl p-6 text-center {type === 'badge' ? 'animate-slideIn' : 'animate-scaleIn'}"
		>
			<!-- Icon circle -->
			{#if type === 'checkmark'}
				<div
					class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900/40 animate-checkDraw"
				>
					<Check class="h-8 w-8 text-emerald-600 dark:text-emerald-400" strokeWidth={3} />
				</div>
			{:else if type === 'badge'}
				<div
					class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/40"
				>
					<FileText class="h-8 w-8 text-blue-600 dark:text-blue-400" />
				</div>
			{:else if type === 'confetti'}
				<div
					class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/40 animate-checkDraw"
				>
					<Target class="h-8 w-8 text-amber-600 dark:text-amber-400" />
				</div>
			{/if}

			<!-- Title -->
			<h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">
				{title}
			</h3>

			<!-- Subtitle -->
			<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
				{subtitle}
			</p>

			<!-- Dismiss hint -->
			<p class="mt-3 text-xs text-slate-400 dark:text-slate-500">
				Cliquez pour fermer
			</p>
		</div>
	</button>
{/if}

<style>
	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes scaleIn {
		from {
			opacity: 0;
			transform: scale(0.9);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateX(-20px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	@keyframes checkDraw {
		from {
			opacity: 0;
			transform: scale(0.5);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}

	@keyframes confettiFall {
		0% {
			transform: translateY(-20px) rotate(0deg);
			opacity: 1;
		}
		100% {
			transform: translateY(100vh) rotate(720deg);
			opacity: 0;
		}
	}

	:global(.animate-fadeIn) {
		animation: fadeIn 0.3s ease-out;
	}

	:global(.animate-scaleIn) {
		animation: scaleIn 0.4s ease-out;
	}

	:global(.animate-slideIn) {
		animation: slideIn 0.4s ease-out;
	}

	:global(.animate-checkDraw) {
		animation: checkDraw 0.5s ease-out;
	}

	:global(.animate-confettiFall) {
		animation: confettiFall 2.5s ease-in forwards;
	}
</style>
