<script lang="ts">
	import { Check, Loader2, X } from 'lucide-svelte';

	interface Props {
		open: boolean;
		planKey: string;
		planName: string;
		planPrice: string;
		planPeriod: string;
		planFeatures: string[];
		loading: boolean;
		onConfirm: () => void;
		onCancel: () => void;
	}

	let {
		open,
		planKey,
		planName,
		planPrice,
		planPeriod,
		planFeatures,
		loading,
		onConfirm,
		onCancel
	}: Props = $props();

	let consentChecked = $state(false);
	let modalEl = $state<HTMLDivElement | null>(null);

	// Reset consent when modal opens
	$effect(() => {
		if (open) {
			consentChecked = false;
		}
	});

	const visibleFeatures = $derived(planFeatures.slice(0, 4));
	const extraCount = $derived(Math.max(0, planFeatures.length - 4));

	function handleKeydown(e: KeyboardEvent) {
		if (!open) return;

		if (e.key === 'Escape' && !loading) {
			e.preventDefault();
			onCancel();
			return;
		}

		// Focus trap
		if (e.key === 'Tab' && modalEl) {
			const focusable = modalEl.querySelectorAll<HTMLElement>(
				'input, button:not([disabled]), a, [tabindex]:not([tabindex="-1"])'
			);
			if (focusable.length === 0) return;

			const first = focusable[0];
			const last = focusable[focusable.length - 1];

			if (e.shiftKey) {
				if (document.activeElement === first) {
					e.preventDefault();
					last.focus();
				}
			} else {
				if (document.activeElement === last) {
					e.preventDefault();
					first.focus();
				}
			}
		}
	}

	function handleBackdropClick() {
		if (!loading) {
			onCancel();
		}
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		role="dialog"
		aria-modal="true"
		aria-labelledby="checkout-confirm-title"
		tabindex="-1"
		class="fixed inset-0 z-50 flex items-center justify-center p-4"
		onkeydown={handleKeydown}
		bind:this={modalEl}
	>
		<!-- Backdrop -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick={handleBackdropClick}></div>

		<!-- Modal card -->
		<div class="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900">
			<!-- Close button -->
			<button
				onclick={onCancel}
				disabled={loading}
				aria-label="Fermer"
				class="absolute right-4 top-4 rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 disabled:opacity-50 dark:hover:bg-slate-800 dark:hover:text-slate-300"
			>
				<X class="h-5 w-5" />
			</button>

			<!-- Title -->
			<h2
				id="checkout-confirm-title"
				class="text-lg font-semibold text-slate-900 dark:text-slate-100"
			>
				Confirmer votre choix
			</h2>

			<!-- Plan recap box -->
			<div class="mt-4 rounded-xl bg-slate-50 p-4 dark:bg-slate-800/50">
				<div class="flex items-baseline justify-between">
					<span class="text-base font-semibold text-slate-900 dark:text-slate-100">
						{planName}
					</span>
					<span class="text-lg font-bold text-blue-600 dark:text-blue-400">
						{planPrice}<span class="text-sm font-normal text-slate-500 dark:text-slate-400">{planPeriod}</span>
					</span>
				</div>

				<ul class="mt-3 space-y-1.5">
					{#each visibleFeatures as feature}
						<li class="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
							<Check class="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
							<span>{feature}</span>
						</li>
					{/each}
					{#if extraCount > 0}
						<li class="text-sm text-slate-400 dark:text-slate-500 pl-6">
							+ {extraCount} autre{extraCount > 1 ? 's' : ''} fonctionnalité{extraCount > 1 ? 's' : ''}
						</li>
					{/if}
				</ul>
			</div>

			<!-- Consent checkbox -->
			<label class="mt-4 flex items-start gap-3 cursor-pointer">
				<input
					type="checkbox"
					bind:checked={consentChecked}
					disabled={loading}
					class="mt-1 h-4 w-4 shrink-0 rounded border-slate-300 text-blue-600 focus:ring-2 focus:ring-blue-500 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800"
				/>
				<span class="text-xs leading-relaxed text-slate-500 dark:text-slate-400">
					Conform&eacute;ment &agrave; l'article L221-28 du Code de la consommation, je souhaite acc&eacute;der imm&eacute;diatement au Service et je reconnais express&eacute;ment renoncer &agrave; mon droit de r&eacute;tractation de 14 jours. Je b&eacute;n&eacute;ficie de la <a href="/cgv#garantie" class="underline text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">garantie satisfait ou rembours&eacute; de 30 jours</a>.
				</span>
			</label>

			<!-- Action buttons -->
			<div class="mt-5 flex items-center gap-3">
				<button
					onclick={onCancel}
					disabled={loading}
					class="flex-1 rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
				>
					Annuler
				</button>
				<button
					onclick={onConfirm}
					disabled={!consentChecked || loading}
					class="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
				>
					{#if loading}
						<Loader2 class="h-4 w-4 animate-spin" />
					{/if}
					Confirmer et payer
				</button>
			</div>

			<!-- Trust footer -->
			<p class="mt-4 text-center text-xs text-slate-400 dark:text-slate-500">
				Paiement s&eacute;curis&eacute; &middot; Garanti 30 jours &middot; Annulation en 1 clic
			</p>
		</div>
	</div>
{/if}
