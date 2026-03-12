<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';

	onMount(() => {
		const sessionId = page.url.searchParams.get('session_id');
		if (sessionId) {
			goto(`/welcome?session_id=${encodeURIComponent(sessionId)}`, { replaceState: true });
		} else {
			goto('/dashboard', { replaceState: true });
		}
	});
</script>

<section class="flex min-h-[50vh] items-center justify-center">
	<p class="text-sm text-slate-500 dark:text-slate-400">Redirection...</p>
</section>
