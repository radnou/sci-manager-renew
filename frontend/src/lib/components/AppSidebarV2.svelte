<script lang="ts">
	import { page } from '$app/state';
	import {
		LayoutDashboard,
		Building2,
		Users,
		FileText,
		TrendingUp,
		Settings,
		ChevronDown,
		LogOut,
		Eye,
		Home,
		Calculator,
		Menu,
		X,
		ChevronsUpDown,
		Check
	} from 'lucide-svelte';
	import { fetchScis, type SCIOverview } from '$lib/api';
	import { supabase } from '$lib/supabase';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import NotificationCenter from '$lib/components/NotificationCenter.svelte';

	interface Props {
		user: { email?: string } | null;
		subscription?: { plan_key: string; plan_name: string } | null;
	}

	let { user, subscription = null }: Props = $props();

	let scis: SCIOverview[] = $state([]);
	let mobileOpen: boolean = $state(false);
	let sciSwitcherOpen: boolean = $state(false);
	let activeSciId: string | null = $state(null);
	let scisLoaded: boolean = $state(false);

	// Fetch SCIs once on mount, and when navigating back to /scis or /dashboard
	$effect(() => {
		const path = page.url.pathname;
		if (!scisLoaded || path === '/scis' || path === '/dashboard') {
			fetchScis()
				.then((data) => {
					scis = data;
					scisLoaded = true;
				})
				.catch(() => {
					scis = [];
				});
		}
	});

	// Auto-detect active SCI from URL
	$effect(() => {
		const match = page.url.pathname.match(/^\/scis\/([^/]+)/);
		activeSciId = match ? match[1] : null;
	});

	const activeSci = $derived(scis.find((s) => String(s.id) === String(activeSciId)) ?? null);

	const sciSubNav = [
		{ suffix: '', label: "Vue d'ensemble", icon: Eye },
		{ suffix: '/biens', label: 'Biens', icon: Home },
		{ suffix: '/associes', label: 'Associés', icon: Users },
		{ suffix: '/fiscalite', label: 'Fiscalité', icon: Calculator },
		{ suffix: '/documents', label: 'Documents', icon: FileText },
		{ suffix: '/settings', label: 'Paramètres', icon: Settings }
	];

	function isActive(href: string): boolean {
		return page.url.pathname === href || (href !== '/' && page.url.pathname.startsWith(`${href}/`));
	}

	function isExactActive(href: string): boolean {
		return page.url.pathname === href;
	}

	async function handleLogout() {
		try {
			await supabase.auth.signOut();
		} catch {
			// Supabase may throw if session already expired
		}
		window.location.href = '/login';
	}

	function closeMobileOnNavigate() {
		mobileOpen = false;
		sciSwitcherOpen = false;
	}

	function selectSci(sciId: string | number) {
		sciSwitcherOpen = false;
		closeMobileOnNavigate();
	}
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
	role={mobileOpen ? 'dialog' : undefined}
	aria-modal={mobileOpen ? 'true' : undefined}
	aria-hidden={mobileOpen ? undefined : 'true'}
	aria-label="Navigation principale"
>
	<!-- SCI Switcher -->
	<div class="flex-shrink-0 border-b border-slate-200 px-3 py-3 dark:border-slate-700">
		{#if activeSci}
			<!-- Active SCI context -->
			<button
				type="button"
				onclick={() => (sciSwitcherOpen = !sciSwitcherOpen)}
				class="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
				aria-haspopup="listbox"
				aria-expanded={sciSwitcherOpen}
				aria-label="Changer de SCI, SCI active: {activeSci.nom}"
			>
				<div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30">
					<Building2 class="h-4 w-4 text-blue-600 dark:text-blue-400" />
				</div>
				<div class="flex-1 min-w-0 text-left">
					<p class="truncate text-sm font-semibold text-slate-900 dark:text-white">{activeSci.nom}</p>
					<p class="text-xs text-slate-500 dark:text-slate-400">
						{subscription?.plan_name ?? 'Free'}
					</p>
				</div>
				<ChevronsUpDown class="h-4 w-4 flex-shrink-0 text-slate-400" />
			</button>
		{:else}
			<!-- No active SCI — show brand + switcher -->
			<button
				type="button"
				onclick={() => (sciSwitcherOpen = !sciSwitcherOpen)}
				class="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
				aria-haspopup="listbox"
				aria-expanded={sciSwitcherOpen}
			>
				<div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800">
					<Building2 class="h-4 w-4 text-slate-600 dark:text-slate-400" />
				</div>
				<div class="flex-1 min-w-0 text-left">
					<p class="text-sm font-semibold text-slate-900 dark:text-white">GererSCI</p>
					<p class="text-xs text-slate-500 dark:text-slate-400">
						{scis.length} SCI{scis.length > 1 ? 's' : ''}
					</p>
				</div>
				<ChevronsUpDown class="h-4 w-4 flex-shrink-0 text-slate-400" />
			</button>
		{/if}

		<!-- SCI Switcher Dropdown -->
		{#if sciSwitcherOpen}
			<button type="button" class="fixed inset-0 z-30" onclick={() => (sciSwitcherOpen = false)} aria-label="Fermer la liste des SCI" tabindex="-1"></button>
			<div
				class="relative z-40 mt-1.5 rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-800"
				role="listbox"
				aria-label="Sélectionner une SCI"
			>
				{#if scis.length === 0}
					<p class="px-3 py-2 text-xs text-slate-400 italic">Aucune SCI</p>
				{/if}
				{#each scis as sci (sci.id)}
					<a
						href="/scis/{sci.id}"
						role="option"
						aria-selected={String(sci.id) === String(activeSciId)}
						class="flex items-center gap-2.5 px-3 py-2 text-sm transition-colors hover:bg-slate-50 dark:hover:bg-slate-700 {String(sci.id) === String(activeSciId) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
						onclick={() => selectSci(sci.id)}
					>
						<Building2 class="h-3.5 w-3.5 flex-shrink-0 {String(sci.id) === String(activeSciId) ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400'}" />
						<span class="flex-1 truncate {String(sci.id) === String(activeSciId) ? 'font-medium text-blue-700 dark:text-blue-300' : 'text-slate-700 dark:text-slate-300'}">{sci.nom}</span>
						{#if String(sci.id) === String(activeSciId)}
							<Check class="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
						{/if}
					</a>
				{/each}
			</div>
		{/if}
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

		<!-- SCI Sub-nav (always visible when a SCI is active) -->
		{#if activeSciId}
			<div class="mt-4">
				<p class="mb-2 px-3 text-xs font-semibold tracking-[0.15em] text-slate-400 uppercase dark:text-slate-500">
					Navigation SCI
				</p>
				<div class="space-y-0.5">
					{#each sciSubNav as subItem (subItem.suffix)}
						{@const href = `/scis/${activeSciId}${subItem.suffix}`}
						{@const active = subItem.suffix === '' ? isExactActive(href) : isActive(href)}
						<a
							{href}
							onclick={closeMobileOnNavigate}
							aria-current={active ? 'page' : undefined}
							class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {active
								? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
								: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
						>
							<subItem.icon class="h-4 w-4 flex-shrink-0" />
							<span>{subItem.label}</span>
						</a>
					{/each}
				</div>
			</div>
		{:else if scis.length > 0}
			<!-- No SCI selected: show SCI list for quick access -->
			<div class="mt-4">
				<p class="mb-2 px-3 text-xs font-semibold tracking-[0.15em] text-slate-400 uppercase dark:text-slate-500">
					Mes SCI
				</p>
				{#each scis as sci (sci.id)}
					<a
						href="/scis/{sci.id}"
						onclick={closeMobileOnNavigate}
						class="mb-0.5 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
					>
						<Building2 class="h-4 w-4 flex-shrink-0" />
						<span class="truncate">{sci.nom}</span>
					</a>
				{/each}
			</div>
		{/if}

		<!-- Gestion -->
		<div class="mt-4">
			<p class="mb-2 px-3 text-xs font-semibold tracking-[0.15em] text-slate-400 uppercase dark:text-slate-500">
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
	</nav>

	<!-- Footer: utilities + user -->
	<div class="flex-shrink-0 border-t border-slate-200 px-3 py-3 dark:border-slate-700">
		<!-- Utilities row -->
		<div class="mb-2 flex items-center gap-1">
			<NotificationCenter />
			<ThemeToggle />
			<a
				href="/settings"
				onclick={closeMobileOnNavigate}
				class="rounded-full p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
				aria-label="Paramètres"
				title="Paramètres"
			>
				<Settings class="h-4 w-4" />
			</a>
		</div>

		<!-- User info + logout -->
		{#if user?.email}
			<p class="mb-1.5 truncate px-2 text-xs text-slate-500 dark:text-slate-400">{user.email}</p>
		{/if}
		<button
			type="button"
			onclick={handleLogout}
			class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm font-medium text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600 dark:text-slate-400 dark:hover:bg-red-900/20 dark:hover:text-red-400"
		>
			<LogOut class="h-3.5 w-3.5 flex-shrink-0" />
			<span>Déconnexion</span>
		</button>
	</div>
</aside>
