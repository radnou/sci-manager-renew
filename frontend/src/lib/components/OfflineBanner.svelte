<script lang="ts">
	import { connectivity, type ConnectivityState } from '$lib/stores/connectivity';
	import { WifiOff, RefreshCw, Wifi } from 'lucide-svelte';
	import { fly } from 'svelte/transition';

	let state: ConnectivityState = $state('online');

	$effect(() => {
		const unsub = connectivity.subscribe((s) => (state = s));
		return unsub;
	});
</script>

{#if state !== 'online'}
	<div
		role="alert"
		aria-live="assertive"
		class="fixed top-0 right-0 left-0 z-[9999] flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium shadow-lg {state === 'offline'
			? 'bg-rose-600 text-white'
			: 'bg-amber-500 text-white'}"
		transition:fly={{ y: -40, duration: 300 }}
	>
		{#if state === 'offline'}
			<WifiOff class="h-4 w-4 shrink-0" />
			<span>Connexion perdue — vos modifications seront synchronisées au retour</span>
		{:else}
			<RefreshCw class="h-4 w-4 shrink-0 animate-spin" />
			<span>Reconnexion en cours…</span>
		{/if}
	</div>
{/if}

{#if state === 'online'}
	<!-- Transient "back online" flash handled by state transition -->
{/if}
