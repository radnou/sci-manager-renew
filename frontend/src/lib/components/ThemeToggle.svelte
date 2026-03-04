<script lang="ts">
	import { theme } from '$lib/stores/theme';
	import { Button } from '$lib/components/ui/button';
	import { Moon, Sun } from 'lucide-svelte';

	let currentTheme = $state('dark');

	// Subscribe to theme changes
	theme.subscribe(value => {
		currentTheme = value;
	});
</script>

<Button
	variant="ghost"
	size="sm"
	onclick={theme.toggle}
	class="group relative h-9 w-9 rounded-full border border-slate-200 bg-white/50 p-0 shadow-sm transition-all duration-300 hover:bg-slate-50 hover:shadow-md dark:border-slate-700 dark:bg-slate-800/50 dark:hover:bg-slate-700"
	aria-label="Basculer le thème"
>
	<div class="relative h-4 w-4">
		<Sun class="absolute inset-0 h-4 w-4 rotate-0 scale-100 transition-all duration-300 group-hover:text-amber-500 dark:-rotate-90 dark:scale-0" />
		<Moon class="absolute inset-0 h-4 w-4 rotate-90 scale-0 transition-all duration-300 group-hover:text-blue-400 dark:rotate-0 dark:scale-100" />
	</div>
	<span class="sr-only">Basculer entre thème clair et sombre</span>
</Button>