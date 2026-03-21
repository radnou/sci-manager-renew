<script lang="ts">
	import { ChevronDown } from 'lucide-svelte';

	interface Props {
		value?: number;
		onchange?: (year: number) => void;
	}

	const currentYear = new Date().getFullYear();

	let { value = currentYear, onchange }: Props = $props();

	const years = Array.from({ length: 6 }, (_, i) => currentYear - i);

	function handleChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		const year = parseInt(target.value, 10);
		onchange?.(year);
	}
</script>

<div class="relative inline-flex items-center">
	<select
		{value}
		onchange={handleChange}
		class="appearance-none rounded-lg border border-slate-200 bg-white py-1.5 pl-3 pr-8 text-sm font-medium text-slate-700 transition-colors hover:border-slate-300 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-slate-600 dark:focus:border-sky-500"
		aria-label="Sélectionner l'année"
	>
		{#each years as year}
			<option value={year}>{year}</option>
		{/each}
	</select>
	<ChevronDown class="pointer-events-none absolute right-2 h-4 w-4 text-slate-400" />
</div>
