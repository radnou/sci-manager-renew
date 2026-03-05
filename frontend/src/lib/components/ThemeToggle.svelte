<script lang="ts">
	import { onDestroy } from 'svelte';
	import { theme } from '$lib/stores/theme';
	import { Button } from '$lib/components/ui/button';
	import { Moon, Sun } from 'lucide-svelte';

	let currentTheme: 'light' | 'dark' = 'dark';
	const unsubscribe = theme.subscribe(value => {
		currentTheme = value;
	});

	onDestroy(unsubscribe);

	function handleToggle() {
		theme.toggle();
	}
</script>

<Button
	variant="outline"
	size="sm"
	onclick={handleToggle}
	class="group relative h-9 w-9 rounded-full border-slate-300 bg-white p-0 text-slate-700 shadow-sm transition-all duration-200 hover:bg-slate-100 hover:text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 dark:hover:text-white"
	aria-label={currentTheme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
	aria-pressed={currentTheme === 'dark'}
	title={currentTheme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
>
	{#if currentTheme === 'dark'}
		<Sun class="h-4 w-4 text-amber-400" />
	{:else}
		<Moon class="h-4 w-4 text-slate-700 dark:text-slate-200" />
	{/if}
	<span class="sr-only">Basculer entre thème clair et sombre</span>
</Button>
