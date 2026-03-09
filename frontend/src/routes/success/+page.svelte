<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button';

	const sessionId = $derived(page.url.searchParams.get('session_id') ?? '');
</script>

<section class="sci-page-shell">
	<div
		class="mx-auto mt-8 max-w-xl rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-8 text-center"
	>
		<p class="sci-eyebrow text-emerald-400">Paiement confirmé</p>
		<h1 class="mt-2 text-3xl font-semibold text-slate-100">Votre abonnement est actif</h1>
		<p class="mt-3 text-slate-300">
			Le paiement Stripe a été accepté. Vous pouvez reprendre le pilotage de votre SCI.
		</p>
		{#if sessionId}
			<p class="mt-4 text-xs text-slate-400">Session Stripe: {sessionId}</p>
		{/if}
		<div class="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
			<Button href="/dashboard">Accéder au dashboard</Button>
			<Button href="/pricing" variant="outline">Retour aux tarifs</Button>
		</div>
	</div>
</section>
