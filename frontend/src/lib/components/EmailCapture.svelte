<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { addToast } from '$lib/components/ui/toast';
	import { Mail, Check } from 'lucide-svelte';

	interface Props {
		source: string;
		title?: string;
		description?: string;
		buttonText?: string;
		context?: Record<string, string>;
		onCaptured?: (email: string) => void;
	}

	let { source, title, description, buttonText = 'Recevoir le résultat', context, onCaptured }: Props =
		$props();

	let email = $state('');
	let consent = $state(false);
	let loading = $state(false);
	let captured = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!email || !consent) return;

		loading = true;
		try {
			const params = new URLSearchParams(window.location.search);
			const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/leads/capture`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					email,
					source,
					utm_source: params.get('utm_source'),
					utm_medium: params.get('utm_medium'),
					utm_campaign: params.get('utm_campaign'),
					context: context || undefined
				})
			});
			if (!res.ok) throw new Error('Erreur');
			captured = true;
			onCaptured?.(email);
		} catch {
			addToast({ title: 'Erreur lors de l\'envoi', variant: 'error' });
		} finally {
			loading = false;
		}
	}
</script>

{#if captured}
	<div
		class="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950/30"
	>
		<Check class="h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
		<p class="text-sm font-medium text-emerald-800 dark:text-emerald-200">
			Résultat envoyé à <strong>{email}</strong>
		</p>
	</div>
{:else}
	<div class="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900">
		{#if title}
			<h3 class="mb-1 text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
		{/if}
		{#if description}
			<p class="mb-4 text-sm text-slate-600 dark:text-slate-400">{description}</p>
		{/if}
		<form onsubmit={handleSubmit} class="space-y-3">
			<div class="flex gap-2">
				<Input
					type="email"
					bind:value={email}
					required
					placeholder="votre@email.fr"
					disabled={loading}
					class="flex-1"
					aria-label="Adresse email"
				/>
				<Button type="submit" disabled={loading || !email || !consent} class="shrink-0">
					<Mail class="mr-2 h-4 w-4" />
					{buttonText}
				</Button>
			</div>
			<label class="flex items-start gap-2 text-xs text-slate-500 dark:text-slate-400">
				<input
					type="checkbox"
					bind:checked={consent}
					class="mt-0.5 rounded border-slate-300"
				/>
				<span>
					J'accepte de recevoir le résultat par email. Conformément au RGPD, vos données ne
					seront utilisées que pour cet envoi.
					<a href="/confidentialite" class="underline hover:text-slate-700 dark:hover:text-slate-300"
						>Politique de confidentialité</a
					>
				</span>
			</label>
		</form>
	</div>
{/if}
