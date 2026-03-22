<script lang="ts">
	import { AlertTriangle, Loader2 } from 'lucide-svelte';

	interface Props {
		open: boolean;
		entityName: string;
		entityType: string;
		warningMessage?: string;
		loading?: boolean;
		onConfirm: () => void;
		onCancel: () => void;
	}

	let {
		open,
		entityName,
		entityType,
		warningMessage = 'Cette action est irr\u00e9versible. Toutes les donn\u00e9es associ\u00e9es seront d\u00e9finitivement supprim\u00e9es.',
		loading = false,
		onConfirm,
		onCancel
	}: Props = $props();

	let confirmInput = $state('');
	let inputEl = $state<HTMLInputElement | null>(null);
	let modalEl = $state<HTMLDivElement | null>(null);

	let isMatch = $derived(
		confirmInput.trim().toLowerCase() === entityName.trim().toLowerCase()
	);

	$effect(() => {
		if (open) {
			confirmInput = '';
			// Focus input after render
			requestAnimationFrame(() => {
				inputEl?.focus();
			});
		}
	});

	function handleKeydown(e: KeyboardEvent) {
		if (!open) return;

		if (e.key === 'Escape' && !loading) {
			e.preventDefault();
			onCancel();
			return;
		}

		if (e.key === 'Enter' && isMatch && !loading) {
			e.preventDefault();
			onConfirm();
			return;
		}

		// Focus trap
		if (e.key === 'Tab' && modalEl) {
			const focusable = modalEl.querySelectorAll<HTMLElement>(
				'input, button:not([disabled]), [tabindex]:not([tabindex="-1"])'
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
		role="alertdialog"
		aria-modal="true"
		aria-labelledby="confirm-delete-title"
		aria-describedby="confirm-delete-desc"
		tabindex="-1"
		class="fixed inset-0 z-50 flex items-center justify-center p-4"
		onkeydown={handleKeydown}
		bind:this={modalEl}
	>
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick={handleBackdropClick}></div>

		<div class="relative w-full max-w-[460px] rounded-2xl border border-rose-200 bg-white p-6 shadow-2xl dark:border-rose-800/60 dark:bg-slate-900">
			<!-- Icon -->
			<div class="mb-4 flex justify-center">
				<div class="flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 dark:bg-rose-900/40">
					<AlertTriangle class="h-6 w-6 text-rose-600 dark:text-rose-400" />
				</div>
			</div>

			<!-- Title -->
			<h2
				id="confirm-delete-title"
				class="text-center text-lg font-semibold text-slate-900 dark:text-slate-100"
			>
				Supprimer {entityType}
			</h2>

			<!-- Warning -->
			<p
				id="confirm-delete-desc"
				class="mt-2 text-center text-sm text-slate-500 dark:text-slate-400"
			>
				{warningMessage}
			</p>

			<!-- Confirmation input -->
			<div class="mt-5 rounded-xl border border-rose-100 bg-rose-50/50 p-4 dark:border-rose-900/40 dark:bg-rose-950/20">
				<label
					for="confirm-delete-input"
					class="mb-2 block text-sm font-medium text-rose-800 dark:text-rose-300"
				>
					Tapez <span class="font-mono font-bold">{entityName}</span> pour confirmer
				</label>
				<input
					id="confirm-delete-input"
					type="text"
					bind:this={inputEl}
					bind:value={confirmInput}
					placeholder={entityName}
					autocomplete="off"
					spellcheck="false"
					disabled={loading}
					class="w-full rounded-lg border border-rose-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-rose-500 focus:ring-2 focus:ring-rose-200 focus:outline-none disabled:opacity-50 dark:border-rose-800 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-rose-800"
				/>
				{#if confirmInput.length > 0 && !isMatch}
					<p class="mt-1.5 text-xs text-rose-500 dark:text-rose-400">
						Le texte ne correspond pas.
					</p>
				{/if}
			</div>

			<!-- Actions -->
			<div class="mt-5 flex items-center justify-end gap-2">
				<button
					onclick={onCancel}
					disabled={loading}
					class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 disabled:opacity-50 dark:text-slate-400 dark:hover:bg-slate-800"
				>
					Annuler
				</button>
				<button
					onclick={onConfirm}
					disabled={!isMatch || loading}
					class="inline-flex items-center gap-2 rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
				>
					{#if loading}
						<Loader2 class="h-4 w-4 animate-spin" />
					{/if}
					Supprimer d\u00e9finitivement
				</button>
			</div>
		</div>
	</div>
{/if}
