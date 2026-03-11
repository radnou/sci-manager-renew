<script lang="ts">
	import { getContext } from 'svelte';
	import { Building2, Users, FileText, MapPin } from 'lucide-svelte';
	import type { SCIDetail } from '$lib/api';

	const sci = getContext<SCIDetail>('sci');
	const sciId = getContext<string>('sciId');
	const userRole = getContext<string>('userRole');
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">SCI</p>
		<h1 class="sci-page-title">{sci.nom}</h1>
		{#if sci.siren}
			<p class="text-sm text-slate-500">SIREN: {sci.siren}</p>
		{/if}
	</header>

	<div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		<a
			href="/scis/{sciId}/biens"
			class="rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950"
		>
			<MapPin class="h-6 w-6 text-blue-600" />
			<p class="mt-3 text-2xl font-bold text-slate-900 dark:text-slate-100">
				{sci.biens_count ?? 0}
			</p>
			<p class="text-sm text-slate-500">Biens</p>
		</a>

		<a
			href="/scis/{sciId}/associes"
			class="rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950"
		>
			<Users class="h-6 w-6 text-purple-600" />
			<p class="mt-3 text-2xl font-bold text-slate-900 dark:text-slate-100">
				{sci.associes_count ?? 0}
			</p>
			<p class="text-sm text-slate-500">Associés</p>
		</a>

		<a
			href="/scis/{sciId}/fiscalite"
			class="rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950"
		>
			<FileText class="h-6 w-6 text-amber-600" />
			<p class="mt-3 text-2xl font-bold text-slate-900 dark:text-slate-100">
				{sci.regime_fiscal ?? '—'}
			</p>
			<p class="text-sm text-slate-500">Régime fiscal</p>
		</a>

		<div
			class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
		>
			<Building2 class="h-6 w-6 text-emerald-600" />
			<p class="mt-3 text-2xl font-bold text-slate-900 dark:text-slate-100">
				{userRole === 'gerant' ? 'Gérant' : 'Associé'}
			</p>
			<p class="text-sm text-slate-500">Votre rôle</p>
		</div>
	</div>
</section>
