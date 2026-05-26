<script lang="ts">
	import { onDestroy } from 'svelte';
	import { theme } from '$lib/stores/theme';
	import { Button } from '$lib/components/ui/button';
	import { Moon, Sun } from 'lucide-svelte';
	import { trackEvent, EVENTS } from '$lib/analytics';

	let currentTheme = $state<'light' | 'dark'>('light');
	const unsubscribe = theme.subscribe(value => {
		currentTheme = value as 'light' | 'dark';
	});

	onDestroy(unsubscribe);

	function handleToggle() {
		theme.toggle();
		trackEvent(EVENTS.THEME_TOGGLE, { theme: currentTheme });
	}

	const themeMeta = $derived.by(() => {
		if (currentTheme === 'dark') {
			return {
				label: 'Thème sombre',
				title: 'Basculer le thème clair',
				icon: Moon
			};
		}
		return {
			label: 'Thème clair',
			title: 'Basculer le thème sombre',
			icon: Sun
		};
	});
</script>

<Button
	variant="outline"
	size="sm"
	onclick={handleToggle}
	class="group relative h-9 w-9 rounded-full border-slate-300 bg-white p-0 text-slate-700 shadow-sm transition-all duration-200 hover:bg-slate-100 hover:text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700 dark:hover:text-white"
	aria-label={themeMeta.label}
	aria-pressed={currentTheme === 'dark'}
	title={themeMeta.title}
>
	<themeMeta.icon class="h-4 w-4 text-slate-700 dark:text-slate-200" />
	<span class="sr-only">{themeMeta.title}</span>
</Button>
