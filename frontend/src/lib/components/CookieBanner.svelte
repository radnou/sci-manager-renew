<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { onMount } from 'svelte';

	let visible = $state(false);

	onMount(() => {
		const consent = localStorage.getItem('cookie-consent');
		visible = !consent;
	});

	function acceptAll() {
		localStorage.setItem('cookie-consent', 'all');
		visible = false;
	}

	function acceptEssential() {
		localStorage.setItem('cookie-consent', 'essential');
		visible = false;
	}
</script>

{#if visible}
	<div class="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 bg-white p-4 shadow-lg dark:border-slate-800 dark:bg-slate-900">
		<div class="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 sm:flex-row">
			<div class="text-sm text-slate-600 dark:text-slate-300">
				<span class="font-semibold">🍪 GérerSCI utilise des cookies</span> — Essentiels (connexion, sécurité), Analytics (anonymisés) et Fonctionnels.
				<a href="/rgpd" class="text-blue-600 underline dark:text-blue-400">En savoir plus</a>
			</div>
			<div class="flex gap-2">
				<Button variant="outline" size="sm" onclick={acceptEssential}>Essentiels uniquement</Button>
				<Button size="sm" onclick={acceptAll}>Tout accepter</Button>
			</div>
		</div>
	</div>
{/if}
