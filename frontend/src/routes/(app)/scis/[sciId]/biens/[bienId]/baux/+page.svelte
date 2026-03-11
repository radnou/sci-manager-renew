<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';

	const sci = getContext<SCIDetail>('sci');
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom} / Biens / Baux</p>
		<h1 class="sci-page-title">Historique des baux</h1>
	</header>
	<p class="text-sm text-slate-500">L'historique des baux sera disponible prochainement.</p>
</section>
