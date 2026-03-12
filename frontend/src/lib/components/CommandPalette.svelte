<script lang="ts">
	import { goto } from '$app/navigation';
	import {
		LayoutDashboard,
		Building2,
		HandCoins,
		FileText,
		Calculator,
		Settings,
		User,
		Search,
		X
	} from 'lucide-svelte';

	let open = $state(false);
	let query = $state('');
	let selectedIndex = $state(0);

	const commands = [
		{ label: 'Dashboard', description: 'Tableau de bord', icon: LayoutDashboard, href: '/dashboard' },
		{ label: 'SCI', description: 'Gérer les sociétés', icon: Building2, href: '/scis' },
		{ label: 'Biens', description: 'Patrimoine immobilier', icon: Building2, href: '/biens' },
		{ label: 'Loyers', description: 'Suivi des encaissements', icon: HandCoins, href: '/loyers' },
		{ label: 'Documents', description: 'Quittances et CERFA', icon: FileText, href: '/documents' },
		{ label: 'Fiscalité', description: 'Exercices et résultats', icon: Calculator, href: '/fiscalite' },
		{ label: 'Tarifs', description: 'Plans et abonnements', icon: HandCoins, href: '/pricing' },
		{ label: 'Paramètres', description: 'Configuration du compte', icon: Settings, href: '/settings' },
		{ label: 'Compte', description: 'Profil utilisateur', icon: User, href: '/account' }
	];

	const filtered = $derived(
		query.trim()
			? commands.filter(
					(c) =>
						c.label.toLowerCase().includes(query.toLowerCase()) ||
						c.description.toLowerCase().includes(query.toLowerCase())
				)
			: commands
	);

	function handleKeydown(event: KeyboardEvent) {
		if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
			event.preventDefault();
			open = !open;
			if (open) {
				query = '';
				selectedIndex = 0;
			}
		}
		if (!open) return;

		if (event.key === 'Escape') {
			open = false;
		} else if (event.key === 'ArrowDown') {
			event.preventDefault();
			selectedIndex = Math.min(selectedIndex + 1, filtered.length - 1);
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			selectedIndex = Math.max(selectedIndex - 1, 0);
		} else if (event.key === 'Enter' && filtered[selectedIndex]) {
			event.preventDefault();
			navigate(filtered[selectedIndex].href);
		}
	}

	function navigate(href: string) {
		open = false;
		query = '';
		goto(href);
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-[100] bg-black/50 backdrop-blur-sm"
		role="presentation"
		onclick={() => (open = false)}
	></div>

	<!-- Palette -->
	<div class="fixed inset-x-0 top-[15vh] z-[101] mx-auto w-full max-w-lg px-4">
		<div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
				<Search class="h-4 w-4 text-slate-400" />
				<input
					type="text"
					bind:value={query}
					placeholder="Rechercher une page..."
					class="flex-1 bg-transparent text-sm text-slate-900 placeholder-slate-400 outline-none dark:text-slate-100"
					autofocus
				/>
				<kbd class="hidden rounded-md border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] font-medium text-slate-500 sm:inline dark:border-slate-700 dark:bg-slate-900">
					Esc
				</kbd>
			</div>

			<div class="max-h-72 overflow-y-auto py-2">
				{#if filtered.length === 0}
					<p class="px-4 py-6 text-center text-sm text-slate-500">Aucun résultat</p>
				{:else}
					{#each filtered as command, i}
						<button
							type="button"
							class="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors {i === selectedIndex
								? 'bg-slate-100 dark:bg-slate-900'
								: 'hover:bg-slate-50 dark:hover:bg-slate-900/50'}"
							onclick={() => navigate(command.href)}
							onmouseenter={() => (selectedIndex = i)}
						>
							<command.icon class="h-4 w-4 flex-shrink-0 text-slate-400" />
							<div class="flex-1">
								<p class="font-medium text-slate-900 dark:text-slate-100">{command.label}</p>
								<p class="text-xs text-slate-500">{command.description}</p>
							</div>
						</button>
					{/each}
				{/if}
			</div>

			<div class="border-t border-slate-200 px-4 py-2 dark:border-slate-800">
				<p class="text-[10px] text-slate-400">
					<kbd class="font-medium">↑↓</kbd> naviguer
					<span class="mx-1.5">·</span>
					<kbd class="font-medium">↵</kbd> ouvrir
					<span class="mx-1.5">·</span>
					<kbd class="font-medium">Esc</kbd> fermer
				</p>
			</div>
		</div>
	</div>
{/if}
