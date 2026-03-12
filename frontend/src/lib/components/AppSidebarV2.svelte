<script lang="ts">
	import { page } from '$app/state';
	import {
		LayoutDashboard,
		Building2,
		Users,
		FileText,
		TrendingUp,
		Settings,
		User,
		ChevronDown,
		LogOut,
		Eye,
		Home,
		Calculator,
		Menu,
		X
	} from 'lucide-svelte';
	import { fetchScis, type SCIOverview } from '$lib/api';
	import { supabase } from '$lib/supabase';

	interface Props {
		user: { email?: string } | null;
	}

	let { user }: Props = $props();

	let scis: SCIOverview[] = $state([]);
	let expandedScis: Set<string | number> = $state(new Set());
	let mobileOpen: boolean = $state(false);

	$effect(() => {
		// Re-fetch SCIs on navigation (reactive dependency on pathname)
		void page.url.pathname;
		fetchScis()
			.then((data) => {
				scis = data;
			})
			.catch(() => {
				scis = [];
			});
	});

	function toggleSci(id: string | number) {
		const next = new Set(expandedScis);
		if (next.has(id)) {
			next.delete(id);
		} else {
			next.add(id);
		}
		expandedScis = next;
	}

	function isActive(href: string): boolean {
		return page.url.pathname === href || (href !== '/' && page.url.pathname.startsWith(`${href}/`));
	}

	function isActiveSci(sciId: string | number): boolean {
		return page.url.pathname.startsWith(`/scis/${sciId}`);
	}

	async function handleLogout() {
		await supabase.auth.signOut();
		window.location.href = '/login';
	}

	function closeMobileOnNavigate() {
		mobileOpen = false;
	}

	const sciSubNav = [
		{ suffix: '', label: "Vue d'ensemble", icon: Eye },
		{ suffix: '/biens', label: 'Biens', icon: Home },
		{ suffix: '/associes', label: 'Associes', icon: Users },
		{ suffix: '/fiscalite', label: 'Fiscalite', icon: Calculator },
		{ suffix: '/documents', label: 'Documents', icon: FileText }
	];
</script>

<!-- Mobile toggle button -->
<button
	type="button"
	class="fixed top-3 left-3 z-50 rounded-lg border border-slate-200 bg-white p-2 shadow-sm md:hidden dark:border-slate-700 dark:bg-slate-800"
	onclick={() => (mobileOpen = !mobileOpen)}
	aria-label={mobileOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
>
	{#if mobileOpen}
		<X class="h-5 w-5 text-slate-600 dark:text-slate-300" />
	{:else}
		<Menu class="h-5 w-5 text-slate-600 dark:text-slate-300" />
	{/if}
</button>

<!-- Mobile backdrop -->
{#if mobileOpen}
	<button
		type="button"
		class="fixed inset-0 z-30 bg-black/40 md:hidden"
		onclick={() => (mobileOpen = false)}
		aria-label="Fermer le menu"
		tabindex="-1"
	></button>
{/if}

<!-- Sidebar -->
<aside
	class="fixed top-0 left-0 z-40 flex h-full w-64 flex-col border-r border-slate-200 bg-white transition-transform duration-200 dark:border-slate-700 dark:bg-slate-900 {mobileOpen
		? 'translate-x-0'
		: '-translate-x-full'} md:relative md:translate-x-0"
>
	<!-- Brand -->
	<div class="flex h-14 flex-shrink-0 items-center border-b border-slate-200 px-4 dark:border-slate-700">
		<a href="/dashboard" class="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
			GererSCI
		</a>
	</div>

	<!-- Navigation -->
	<nav class="flex-1 overflow-y-auto px-3 py-4">
		<!-- Dashboard -->
		<a
			href="/dashboard"
			onclick={closeMobileOnNavigate}
			aria-current={isActive('/dashboard') ? 'page' : undefined}
			class="mb-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {isActive(
				'/dashboard'
			)
				? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
				: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
		>
			<LayoutDashboard class="h-4 w-4 flex-shrink-0" />
			<span>Dashboard</span>
		</a>

		<!-- Mes SCI section -->
		<div class="mt-4">
			<p class="mb-2 px-3 text-[0.65rem] font-semibold tracking-[0.15em] text-slate-400 uppercase dark:text-slate-500">
				Mes SCI
			</p>

			{#if scis.length === 0}
				<p class="px-3 py-2 text-xs text-slate-400 italic dark:text-slate-500">Aucune SCI</p>
			{/if}

			{#each scis as sci (sci.id)}
				<div class="mb-0.5">
					<!-- SCI expandable header -->
					<button
						type="button"
						onclick={() => toggleSci(sci.id)}
						class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors {isActiveSci(
							sci.id
						)
							? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
							: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
					>
						<Building2 class="h-4 w-4 flex-shrink-0" />
						<span class="flex-1 truncate text-left">{sci.nom}</span>
						<ChevronDown
							class="h-3.5 w-3.5 flex-shrink-0 transition-transform duration-200 {expandedScis.has(
								sci.id
							)
								? 'rotate-180'
								: 'rotate-0'}"
						/>
					</button>

					<!-- Sub-nav items -->
					{#if expandedScis.has(sci.id)}
						<div class="ml-4 mt-0.5 space-y-0.5 border-l border-slate-200 pl-3 dark:border-slate-700">
							{#each sciSubNav as subItem (subItem.suffix)}
								{@const href = `/scis/${sci.id}${subItem.suffix}`}
								<a
									{href}
									onclick={closeMobileOnNavigate}
									aria-current={page.url.pathname === href ? 'page' : undefined}
									class="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[0.8rem] transition-colors {page
										.url.pathname === href
										? 'bg-slate-100 font-medium text-slate-900 dark:bg-slate-800 dark:text-white'
										: 'text-slate-500 hover:bg-slate-50 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-300'}"
								>
									<subItem.icon class="h-3.5 w-3.5 flex-shrink-0" />
									<span>{subItem.label}</span>
								</a>
							{/each}
						</div>
					{/if}
				</div>
			{/each}
		</div>

		<!-- Finances -->
		<div class="mt-4">
			<p class="mb-2 px-3 text-[0.65rem] font-semibold tracking-[0.15em] text-slate-400 uppercase dark:text-slate-500">
				Gestion
			</p>
			<a
				href="/finances"
				onclick={closeMobileOnNavigate}
				aria-current={isActive('/finances') ? 'page' : undefined}
				class="mb-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {isActive(
					'/finances'
				)
					? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
					: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
			>
				<TrendingUp class="h-4 w-4 flex-shrink-0" />
				<span>Finances</span>
			</a>
		</div>

		<!-- Compte section -->
		<div class="mt-4">
			<p class="mb-2 px-3 text-[0.65rem] font-semibold tracking-[0.15em] text-slate-400 uppercase dark:text-slate-500">
				Compte
			</p>
			<a
				href="/settings"
				onclick={closeMobileOnNavigate}
				aria-current={isActive('/settings') ? 'page' : undefined}
				class="mb-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {isActive(
					'/settings'
				)
					? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
					: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
			>
				<Settings class="h-4 w-4 flex-shrink-0" />
				<span>Parametres</span>
			</a>
			<a
				href="/account"
				onclick={closeMobileOnNavigate}
				aria-current={isActive('/account') ? 'page' : undefined}
				class="mb-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {isActive(
					'/account'
				)
					? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
					: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
			>
				<User class="h-4 w-4 flex-shrink-0" />
				<span>Compte</span>
			</a>
		</div>
	</nav>

	<!-- User footer -->
	<div class="flex-shrink-0 border-t border-slate-200 px-3 py-3 dark:border-slate-700">
		{#if user?.email}
			<p class="mb-2 truncate text-xs text-slate-500 dark:text-slate-400">{user.email}</p>
		{/if}
		<button
			type="button"
			onclick={handleLogout}
			class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-red-50 hover:text-red-600 dark:text-slate-400 dark:hover:bg-red-900/20 dark:hover:text-red-400"
		>
			<LogOut class="h-4 w-4 flex-shrink-0" />
			<span>Deconnexion</span>
		</button>
	</div>
</aside>
