<script lang="ts">
	import { page } from '$app/state';
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';

	const sci = getContext<SCIDetail>('sci');
	const bienId = $derived(page.params.bienId);
	const bien = $derived(sci.biens?.find((b) => String(b.id) === bienId));
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom} / Biens</p>
		<h1 class="sci-page-title">{bien?.adresse ?? 'Bien'}</h1>
		{#if bien}
			<p class="text-sm text-slate-500">{bien.ville} {bien.code_postal}</p>
		{/if}
	</header>

	{#if bien}
		<div class="mt-6 space-y-6">
			<!-- Section A: Identité -->
			<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
				<h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Identité du bien</h2>
				<div class="grid gap-4 sm:grid-cols-2">
					<div>
						<p class="text-xs text-slate-500">Adresse</p>
						<p class="text-sm font-medium text-slate-900 dark:text-slate-100">{bien.adresse}</p>
					</div>
					<div>
						<p class="text-xs text-slate-500">Ville</p>
						<p class="text-sm font-medium text-slate-900 dark:text-slate-100">{bien.ville} {bien.code_postal}</p>
					</div>
					<div>
						<p class="text-xs text-slate-500">Type locatif</p>
						<p class="text-sm font-medium text-slate-900 dark:text-slate-100">{bien.type_locatif ?? '—'}</p>
					</div>
					<div>
						<p class="text-xs text-slate-500">Loyer CC</p>
						<p class="text-sm font-medium text-slate-900 dark:text-slate-100">{bien.loyer_cc ?? 0}€/mois</p>
					</div>
				</div>
			</div>

			<!-- Section C: Loyers (placeholder — Sprint 3) -->
			<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
				<h2 class="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Loyers</h2>
				<p class="text-sm text-slate-500">Les loyers de ce bien seront affichés ici.</p>
			</div>
		</div>
	{:else}
		<p class="mt-6 text-sm text-rose-600">Bien non trouvé.</p>
	{/if}
</section>
