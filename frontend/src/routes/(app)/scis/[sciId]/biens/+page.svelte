<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';

	const sci = getContext<SCIDetail>('sci');
	const sciId = getContext<string>('sciId');
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<h1 class="sci-page-title">Biens</h1>
	</header>

	{#if sci.biens && sci.biens.length > 0}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each sci.biens as bien (String(bien.id))}
				<a
					href="/scis/{sciId}/biens/{bien.id}"
					class="group rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950"
				>
					<h3 class="font-semibold text-slate-900 dark:text-slate-100">{bien.adresse}</h3>
					<p class="mt-1 text-sm text-slate-500">
						{bien.ville} {bien.code_postal}
					</p>
					<div class="mt-3 flex gap-4 text-xs text-slate-500">
						{#if bien.type_locatif}
							<span class="rounded-full bg-slate-100 px-2 py-0.5 dark:bg-slate-800">
								{bien.type_locatif}
							</span>
						{/if}
						{#if bien.loyer_cc}
							<span>{bien.loyer_cc}€/mois</span>
						{/if}
					</div>
				</a>
			{/each}
		</div>
	{:else}
		<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 py-16 dark:border-slate-700">
			<p class="text-sm text-slate-500">Aucun bien. Ajoutez votre premier bien.</p>
		</div>
	{/if}
</section>
