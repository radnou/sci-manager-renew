<script lang="ts">
	import { Search } from 'lucide-svelte';
</script>

<div class="border-b border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30">
	<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6 lg:px-8">
		<div class="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-300">
			<Search class="h-4 w-4 flex-shrink-0" />
			<span>Vous explorez des données de démonstration. Souscrivez pour gérer vos vraies SCI.</span>
		</div>
		<a href="/pricing" class="flex-shrink-0 rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-700">
			Souscrire →
		</a>
	</div>
</div>
