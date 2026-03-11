<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';

	const sci = getContext<SCIDetail>('sci');
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<h1 class="sci-page-title">Associés</h1>
	</header>

	{#if sci.associes && sci.associes.length > 0}
		<div class="space-y-3">
			{#each sci.associes as associe (String(associe.id))}
				<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
					<div class="flex items-center justify-between">
						<div>
							<p class="font-medium text-slate-900 dark:text-slate-100">{associe.nom}</p>
							{#if associe.email}
								<p class="text-sm text-slate-500">{associe.email}</p>
							{/if}
						</div>
						<span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium dark:bg-slate-800">
							{associe.role ?? 'associé'} — {associe.part ?? 0}%
						</span>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<p class="text-sm text-slate-500">Aucun associé.</p>
	{/if}
</section>
