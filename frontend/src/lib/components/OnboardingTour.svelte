<script lang="ts">
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import {
		LayoutDashboard,
		Building2,
		Home,
		FileText,
		CalendarClock,
		TrendingUp,
		X,
		ChevronRight,
		ChevronLeft
	} from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';

	const STORAGE_KEY = 'gerersci_tour_completed';

	interface TourStep {
		icon: typeof LayoutDashboard;
		iconColor: string;
		iconBg: string;
		title: string;
		description: string;
	}

	const steps: TourStep[] = [
		{
			icon: LayoutDashboard,
			iconColor: 'text-blue-500 dark:text-blue-400',
			iconBg: 'bg-blue-100 dark:bg-blue-950/50',
			title: 'Vos SCI et biens',
			description:
				'Votre tableau de bord centralise les KPIs de toutes vos SCI. Chaque SCI a ses biens, associés, fiscalité et documents — le tout en un seul endroit.'
		},
		{
			icon: Home,
			iconColor: 'text-emerald-500 dark:text-emerald-400',
			iconBg: 'bg-emerald-100 dark:bg-emerald-950/50',
			title: 'Gestion locative',
			description:
				'Chaque bien a 9 onglets : identité, bail, loyers, charges, assurance PNO, agence, rentabilité, documents et événements. Vos quittances PDF conformes sont générées en 1 clic.'
		},
		{
			icon: CalendarClock,
			iconColor: 'text-amber-500 dark:text-amber-400',
			iconBg: 'bg-amber-100 dark:bg-amber-950/50',
			title: 'Échéances et finances',
			description:
				'Recevez une alerte avant chaque échéance importante : bail, assurance, déclaration fiscale, AG. La vue finances consolide vos revenus et charges sur toutes vos SCI.'
		},
		{
			icon: TrendingUp,
			iconColor: 'text-sky-500 dark:text-sky-400',
			iconBg: 'bg-sky-100 dark:bg-sky-950/50',
			title: 'Prêt à commencer',
			description:
				'Rendez-vous dans « Mes SCI » pour créer votre première société, puis ajoutez vos biens et locataires. En 5 minutes, vous êtes opérationnel.'
		}
	];

	let visible = $state(false);
	let currentStep = $state(0);
	let dontShowAgain = $state(false);
	let dialogEl: HTMLDivElement | undefined = $state(undefined);

	const step = $derived(steps[currentStep]);
	const isFirst = $derived(currentStep === 0);
	const isLast = $derived(currentStep === steps.length - 1);

	export function open() {
		currentStep = 0;
		dontShowAgain = false;
		visible = true;
	}

	onMount(() => {
		try {
			if (localStorage.getItem('gerersci.e2e-fake-session')) {
				return;
			}
			const completed = localStorage.getItem(STORAGE_KEY);
			if (completed !== 'true') {
				visible = true;
			}
		} catch {
			// localStorage unavailable (private browsing) — show tour
			visible = true;
		}
	});

	// Focus the dialog when it becomes visible
	$effect(() => {
		if (visible && dialogEl) {
			dialogEl.focus();
		}
	});

	function dismiss() {
		try { localStorage.setItem(STORAGE_KEY, 'true'); } catch { /* noop */ }
		visible = false;
	}

	function close() {
		// Session-only close — tour will reappear next visit
		visible = false;
	}

	function next() {
		if (isLast) {
			if (dontShowAgain) {
				dismiss();
			} else {
				dismiss(); // "Commencer" always dismisses — user finished the tour
			}
		} else {
			currentStep++;
		}
	}

	function prev() {
		if (!isFirst) {
			currentStep--;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (!visible) return;
		if (event.key === 'Escape') {
			close(); // Escape = soft close, not permanent dismiss
		} else if (event.key === 'ArrowRight') {
			next();
		} else if (event.key === 'ArrowLeft') {
			prev();
		}
	}

	function handleFocusTrap(event: KeyboardEvent) {
		if (event.key !== 'Tab' || !dialogEl) return;
		const focusable = dialogEl.querySelectorAll<HTMLElement>(
			'button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
		);
		if (focusable.length === 0) return;
		const first = focusable[0];
		const last = focusable[focusable.length - 1];
		if (event.shiftKey && document.activeElement === first) {
			event.preventDefault();
			last.focus();
		} else if (!event.shiftKey && document.activeElement === last) {
			event.preventDefault();
			first.focus();
		}
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			close(); // Backdrop click = soft close
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if visible}
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
		onclick={handleBackdropClick}
		onkeydown={(e) => { if (e.key === 'Escape') close(); }}
		transition:fade={{ duration: 200 }}
	>
		<!-- Dialog panel (role="dialog" on the card, not the backdrop) -->
		<div
			bind:this={dialogEl}
			role="dialog"
			aria-modal="true"
			aria-labelledby="tour-title"
			tabindex="-1"
			class="relative w-full max-w-lg rounded-2xl border border-slate-200 bg-white shadow-2xl outline-none dark:border-slate-700 dark:bg-slate-900"
			onkeydown={handleFocusTrap}
		>
			<!-- Close button -->
			<button
				type="button"
				class="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
				onclick={close}
				aria-label="Fermer la visite guidée"
			>
				<X class="h-4 w-4" />
			</button>

			<!-- Step indicator -->
			<div class="px-6 pt-5">
				<span class="text-xs font-semibold tracking-wider text-slate-400 uppercase dark:text-slate-500">
					{currentStep + 1} / {steps.length}
				</span>
			</div>

			<!-- Content -->
			{#key currentStep}
				<div class="px-6 pb-2 pt-4" in:fade={{ duration: 180 }}>
					<div class="flex flex-col items-center text-center">
						<div
							class="flex h-16 w-16 items-center justify-center rounded-2xl {step.iconBg}"
						>
							<step.icon class="h-8 w-8 {step.iconColor}" aria-hidden="true" />
						</div>
						<h2 id="tour-title" class="mt-5 text-xl font-bold text-slate-900 dark:text-slate-100">
							{step.title}
						</h2>
						<p class="mt-3 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
							{step.description}
						</p>
					</div>
				</div>
			{/key}

			<!-- Dont show again (last step only) -->
			{#if isLast}
				<div class="flex justify-center px-6 pt-2">
					<label class="flex cursor-pointer select-none items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
						<input
							type="checkbox"
							bind:checked={dontShowAgain}
							class="h-3.5 w-3.5 rounded border-slate-300 dark:border-slate-600"
						/>
						Ne plus afficher
					</label>
				</div>
			{/if}

			<!-- Progress dots -->
			<div class="flex justify-center gap-1.5 px-6 pt-5">
				{#each steps as _, i}
					<button
						type="button"
						class="h-2 rounded-full transition-all duration-200 {i === currentStep
							? 'w-6 bg-blue-500 dark:bg-blue-400'
							: 'w-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600'}"
						onclick={() => (currentStep = i)}
						aria-label="Aller à l'étape {i + 1}"
					></button>
				{/each}
			</div>

			<!-- Actions -->
			<div class="flex items-center justify-between gap-3 px-6 pb-6 pt-5">
				<Button variant="ghost" onclick={dismiss} class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
					Passer
				</Button>

				<div class="flex items-center gap-2">
					{#if !isFirst}
						<Button variant="outline" onclick={prev} size="sm">
							<ChevronLeft class="h-4 w-4" aria-hidden="true" />
							Précédent
						</Button>
					{/if}
					<Button onclick={next} size="sm">
						{#if isLast}
							Commencer
						{:else}
							Suivant
							<ChevronRight class="h-4 w-4" aria-hidden="true" />
						{/if}
					</Button>
				</div>
			</div>
		</div>
	</div>
{/if}
