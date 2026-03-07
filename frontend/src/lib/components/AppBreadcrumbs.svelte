<script lang="ts">
	import { page } from '$app/state';
	import { ChevronRight, House } from 'lucide-svelte';

	type Crumb = {
		label: string;
		href: string;
	};

	const labelMap: Record<string, string> = {
		dashboard: 'Cockpit',
		scis: 'Portefeuille',
		exploitation: 'Exploitation',
		finance: 'Finance',
		biens: 'Biens',
		associes: 'Associés',
		charges: 'Charges',
		fiscalite: 'Fiscalité',
		loyers: 'Loyers',
		pricing: 'Offre et facturation',
		login: 'Connexion',
		register: 'Inscription',
		privacy: 'Confidentialité',
		account: 'Compte',
		settings: 'Paramètres'
	};

	function buildBreadcrumbs(pathname: string): Crumb[] {
		const segments = pathname.split('/').filter(Boolean);
		const crumbs: Crumb[] = [{ label: 'Accueil', href: '/' }];
		let currentPath = '';

		for (const segment of segments) {
			currentPath = `${currentPath}/${segment}`;
			crumbs.push({
				label: labelMap[segment] ?? segment,
				href: currentPath
			});
		}

		return crumbs;
	}

	const breadcrumbs = $derived(buildBreadcrumbs(page.url.pathname));
</script>

<nav
	aria-label="Fil d’Ariane"
	class="mx-auto flex w-full max-w-7xl items-center px-4 pb-3 text-sm text-slate-500 md:px-8"
>
	<ol class="flex min-w-0 flex-wrap items-center gap-2">
		{#each breadcrumbs as crumb, index (crumb.href)}
			<li class="flex items-center gap-2">
				{#if index > 0}
					<ChevronRight class="h-4 w-4 shrink-0 text-slate-400" />
				{/if}

				{#if index === 0}
					<a
						href={crumb.href}
						class="inline-flex items-center gap-1 rounded-full px-2 py-1 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800"
					>
						<House class="h-3.5 w-3.5" />
						<span>{crumb.label}</span>
					</a>
				{:else if index === breadcrumbs.length - 1}
					<span class="truncate font-medium text-slate-700 dark:text-slate-200">{crumb.label}</span>
				{:else}
					<a
						href={crumb.href}
						class="truncate rounded-full px-2 py-1 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800"
					>
						{crumb.label}
					</a>
				{/if}
			</li>
		{/each}
	</ol>
</nav>
