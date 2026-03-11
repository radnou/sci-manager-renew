<script lang="ts">
	import { getContext } from 'svelte';
	import type { SCIDetail } from '$lib/api';

	const sci = getContext<SCIDetail>('sci');
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<h1 class="sci-page-title">Fiscalité</h1>
	</header>
	<p class="text-sm text-slate-500">La vue fiscalité sera migrée ici prochainement.</p>
</section>
