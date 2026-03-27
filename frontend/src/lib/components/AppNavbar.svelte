<script lang="ts">
	import { page } from '$app/state';
	import {
		LayoutDashboard,
		Building2,
		TrendingUp,
		FileSpreadsheet,
		Settings,
		User,
		LogOut,
		Eye,
		Home,
		Users,
		Calculator,
		FileText,
		ChevronDown,
		ChevronRight,
		Check,
		House,
		Briefcase,
		CalendarClock,
		ArrowLeftRight,
		Gavel,
		Menu,
		X
	} from 'lucide-svelte';
	import { fetchScis, type SCIOverview } from '$lib/api';
	import { supabase } from '$lib/supabase';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import NotificationCenter from '$lib/components/NotificationCenter.svelte';
	import { breadcrumbNames } from '$lib/stores/breadcrumb-names';

	interface Props {
		user: { email?: string } | null;
		subscription?: { plan_key: string; plan_name: string } | null;
	}

	let { user, subscription = null }: Props = $props();

	let scis: SCIOverview[] = $state([]);
	let sciSwitcherOpen: boolean = $state(false);
	let accountMenuOpen: boolean = $state(false);
	let mobileMenuOpen: boolean = $state(false);
	let activeSciId: string | null = $state(null);
	let scisLoaded: boolean = $state(false);
	let accountMenuContainer = $state<HTMLDivElement | null>(null);
	let sciSwitcherContainer = $state<HTMLDivElement | null>(null);
	let mobileDrawerContainer = $state<HTMLDivElement | null>(null);
	let loggingOut = $state(false);

	// Fetch SCIs once, refresh on /scis or /dashboard
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

	// Close dropdowns on outside click
	$effect(() => {
		const handleClick = (e: MouseEvent) => {
			if (accountMenuContainer && !accountMenuContainer.contains(e.target as Node)) {
				accountMenuOpen = false;
			}
			if (sciSwitcherContainer && !sciSwitcherContainer.contains(e.target as Node)) {
				sciSwitcherOpen = false;
			}
		};
		document.addEventListener('mousedown', handleClick);
		return () => document.removeEventListener('mousedown', handleClick);
	});

	// Lock body scroll when mobile menu is open
	$effect(() => {
		if (mobileMenuOpen) {
			document.body.style.overflow = 'hidden';
		} else {
			document.body.style.overflow = '';
		}
		return () => {
			document.body.style.overflow = '';
		};
	});

	// Close mobile menu on route change
	$effect(() => {
		page.url.pathname;
		mobileMenuOpen = false;
	});

	function closeMobileMenu() {
		mobileMenuOpen = false;
	}

	const activeSci = $derived(scis.find((s) => String(s.id) === String(activeSciId)) ?? null);

	const sciSubNav = [
		{ suffix: '', label: "Vue d'ensemble", icon: Eye },
		{ suffix: '/biens', label: 'Biens', icon: Home },
		{ suffix: '/associes', label: 'Associés', icon: Users },
		{ suffix: '/fiscalite', label: 'Fiscalité', icon: Calculator },
		{ suffix: '/mouvements-parts', label: 'Parts', icon: ArrowLeftRight },
		{ suffix: '/assemblees-generales', label: 'AG', icon: Gavel },
		{ suffix: '/documents', label: 'Documents', icon: FileText }
	];

	function isActive(href: string): boolean {
		return page.url.pathname === href || (href !== '/' && page.url.pathname.startsWith(`${href}/`));
	}

	function isExactActive(href: string): boolean {
		return page.url.pathname === href;
	}

	async function handleLogout() {
		loggingOut = true;
		accountMenuOpen = false;
		try {
			await supabase.auth.signOut();
		} catch {
			// Supabase may throw if session already expired
		}
		// Brief visual feedback before redirect
		await new Promise((r) => setTimeout(r, 500));
		window.location.href = '/';
	}

	// Breadcrumbs
	const labelMap: Record<string, string> = {
		dashboard: 'Tableau de bord',
		scis: 'Portefeuille',
		finances: 'Finances',
		bilans: 'Bilans',
		biens: 'Biens',
		associes: 'Associés',
		charges: 'Charges',
		fiscalite: 'Fiscalité',
		loyers: 'Loyers',
		documents: 'Documents',
		baux: 'Baux',
		onboarding: 'Onboarding',
		admin: 'Admin',
		account: 'Compte',
		billing: 'Abonnement',
		settings: 'Paramètres',
		'assemblees-generales': 'Assemblées générales'
	};

	type Crumb = { label: string; href: string };

	const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

	function buildBreadcrumbs(pathname: string, names: Record<string, string>): Crumb[] {
		const segments = pathname.split('/').filter(Boolean);
		const crumbs: Crumb[] = [];
		let currentPath = '';
		for (const segment of segments) {
			currentPath = `${currentPath}/${segment}`;
			let label = names[segment] ?? labelMap[segment];
			// If the segment is a UUID with no mapped name, show a loading placeholder
			if (!label) {
				label = UUID_RE.test(segment) ? '…' : segment;
			}
			crumbs.push({ label, href: currentPath });
		}
		return crumbs;
	}

	const breadcrumbs = $derived(buildBreadcrumbs(page.url.pathname, $breadcrumbNames));
</script>

<!-- Primary navbar -->
<nav
	class="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/95"
>
	<div class="mx-auto flex w-full max-w-7xl items-center gap-2 px-4 py-2.5 md:px-8">
		<!-- Logo -->
		<a
			href="/dashboard"
			class="mr-4 text-lg font-bold tracking-tight text-slate-900 transition-colors hover:text-blue-600 dark:text-slate-100 dark:hover:text-blue-400"
		>
			GérerSCI
		</a>

		<!-- Hamburger button (mobile only) -->
		<button
			type="button"
			class="inline-flex items-center justify-center rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 md:hidden dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
			onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
			aria-label={mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
			aria-expanded={mobileMenuOpen}
			aria-controls="mobile-drawer"
		>
			{#if mobileMenuOpen}
				<X class="h-5 w-5" />
			{:else}
				<Menu class="h-5 w-5" />
			{/if}
		</button>

		<!-- Main nav links (hidden on mobile) -->
		<a
			href="/dashboard"
			class="hidden items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors md:flex {isActive('/dashboard')
				? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
				: 'text-slate-500 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
		>
			<LayoutDashboard class="h-4 w-4" />
			<span class="hidden sm:inline">Tableau de bord</span>
		</a>

		<!-- SCI Switcher (hidden on mobile) -->
		<div class="relative hidden md:block" bind:this={sciSwitcherContainer}>
			<button
				type="button"
				onclick={() => (sciSwitcherOpen = !sciSwitcherOpen)}
				class="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors {activeSciId
					? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
					: 'text-slate-500 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
				aria-haspopup="listbox"
				aria-expanded={sciSwitcherOpen}
			>
				<Building2 class="h-4 w-4" />
				<span class="hidden sm:inline">{activeSci?.nom ?? 'Mes SCI'}</span>
				<ChevronDown class="h-3.5 w-3.5 transition-transform {sciSwitcherOpen ? 'rotate-180' : ''}" />
			</button>

			{#if sciSwitcherOpen}
				<div
					class="absolute left-0 top-full z-50 mt-1.5 w-64 rounded-xl border border-slate-200 bg-white py-1.5 shadow-lg dark:border-slate-700 dark:bg-slate-900"
					role="listbox"
					aria-label="Sélectionner une SCI"
				>
					{#if scis.length === 0}
						<p class="px-3 py-2 text-xs text-slate-400 italic">Aucune SCI</p>
					{/if}
					{#each scis as sci (sci.id)}
						<a
							href={`/scis/${sci.id}`}
							role="option"
							aria-selected={String(sci.id) === String(activeSciId)}
							class="flex items-center gap-2.5 px-3 py-2 text-sm transition-colors hover:bg-slate-50 dark:hover:bg-slate-800 {String(sci.id) === String(activeSciId) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
							onclick={() => (sciSwitcherOpen = false)}
						>
							<Building2 class="h-3.5 w-3.5 flex-shrink-0 {String(sci.id) === String(activeSciId) ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400'}" />
							<span class="flex-1 truncate {String(sci.id) === String(activeSciId) ? 'font-medium text-blue-700 dark:text-blue-300' : 'text-slate-700 dark:text-slate-300'}">{sci.nom}</span>
							{#if String(sci.id) === String(activeSciId)}
								<Check class="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
							{/if}
						</a>
					{/each}
					<div class="mt-1 border-t border-slate-100 pt-1 dark:border-slate-800">
						<a
							href="/scis"
							class="flex items-center gap-2 px-3 py-2 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-300"
							onclick={() => (sciSwitcherOpen = false)}
						>
							Voir toutes les SCI
						</a>
					</div>
				</div>
			{/if}
		</div>

		<a
			href="/exploitation"
			class="hidden items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors md:flex {isActive('/exploitation')
				? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
				: 'text-slate-500 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
		>
			<Briefcase class="h-4 w-4" />
			<span>Exploitation</span>
		</a>
		<a
			href="/echeances"
			class="hidden items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors md:flex {isActive('/echeances')
				? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
				: 'text-slate-500 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
		>
			<CalendarClock class="h-4 w-4" />
			<span>Échéances</span>
		</a>
		<a
			href="/finances"
			class="hidden items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors md:flex {isActive('/finances')
				? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
				: 'text-slate-500 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
		>
			<TrendingUp class="h-4 w-4" />
			<span class="hidden sm:inline">Finances</span>
		</a>
		<a
			href="/bilans"
			class="hidden items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors md:flex {isActive('/bilans')
				? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
				: 'text-slate-500 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
		>
			<FileSpreadsheet class="h-4 w-4" />
			<span class="hidden sm:inline">Bilans</span>
		</a>

		<!-- Spacer -->
		<div class="flex-1"></div>

		<!-- Right side: utilities -->
		<div class="flex items-center gap-1.5">
			<NotificationCenter />
			<div class="hidden md:block">
				<ThemeToggle />
			</div>

			<!-- Account dropdown -->
			<div class="relative ml-1" bind:this={accountMenuContainer}>
				<button
					type="button"
					onclick={() => (accountMenuOpen = !accountMenuOpen)}
					class="flex items-center gap-2 rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm transition-colors hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
					aria-haspopup="menu"
					aria-expanded={accountMenuOpen}
				>
					<span class="hidden max-w-[10rem] truncate text-slate-600 md:block dark:text-slate-300">{user?.email ?? ''}</span>
					<User class="h-4 w-4 text-slate-500" />
				</button>

				{#if accountMenuOpen}
					<div
						class="absolute right-0 top-full z-50 mt-1.5 w-56 rounded-xl border border-slate-200 bg-white py-1.5 shadow-lg dark:border-slate-700 dark:bg-slate-900"
						role="menu"
					>
						<div class="border-b border-slate-100 px-3 py-2 dark:border-slate-800">
							<p class="truncate text-sm font-medium text-slate-900 dark:text-white">{user?.email}</p>
							<p class="text-xs text-slate-500">{subscription?.plan_name ?? 'Free'}</p>
						</div>
						<a
							href="/settings"
							role="menuitem"
							class="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
							onclick={() => (accountMenuOpen = false)}
						>
							<Settings class="h-3.5 w-3.5" />
							Paramètres
						</a>
						<div class="border-t border-slate-100 pt-1 dark:border-slate-800">
							{#if loggingOut}
								<span class="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-500 dark:text-slate-400">
									<LogOut class="h-3.5 w-3.5 animate-pulse" />
									Déconnexion en cours…
								</span>
							{:else}
								<button
									type="button"
									role="menuitem"
									onclick={handleLogout}
									class="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
								>
									<LogOut class="h-3.5 w-3.5" />
									Déconnexion
								</button>
							{/if}
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>

	<!-- Mobile drawer overlay -->
	{#if mobileMenuOpen}
		<!-- Backdrop -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity md:hidden"
			onclick={closeMobileMenu}
			onkeydown={(e) => e.key === 'Escape' && closeMobileMenu()}
		></div>

		<!-- Drawer panel -->
		<div
			bind:this={mobileDrawerContainer}
			id="mobile-drawer"
			class="fixed inset-y-0 left-0 z-50 flex w-72 flex-col overflow-y-auto border-r border-slate-200 bg-white shadow-xl md:hidden dark:border-slate-800 dark:bg-slate-950"
			role="dialog"
			aria-modal="true"
			aria-label="Menu de navigation"
			style="animation: slideInLeft 200ms ease-out;"
		>
			<!-- Drawer header -->
			<div class="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
				<a href="/dashboard" class="text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100" onclick={closeMobileMenu}>
					GérerSCI
				</a>
				<button
					type="button"
					class="rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
					onclick={closeMobileMenu}
					aria-label="Fermer le menu"
				>
					<X class="h-5 w-5" />
				</button>
			</div>

			<!-- Nav links -->
			<div class="flex flex-1 flex-col gap-1 px-3 py-4">
				<p class="mb-1 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Navigation</p>
				<a
					href="/dashboard"
					class="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors {isActive('/dashboard')
						? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
						: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
					onclick={closeMobileMenu}
				>
					<LayoutDashboard class="h-4.5 w-4.5" />
					Tableau de bord
				</a>
				<a
					href="/exploitation"
					class="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors {isActive('/exploitation')
						? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
						: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
					onclick={closeMobileMenu}
				>
					<Briefcase class="h-4.5 w-4.5" />
					Exploitation
				</a>
				<a
					href="/echeances"
					class="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors {isActive('/echeances')
						? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
						: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
					onclick={closeMobileMenu}
				>
					<CalendarClock class="h-4.5 w-4.5" />
					Échéances
				</a>
				<a
					href="/finances"
					class="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors {isActive('/finances')
						? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
						: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
					onclick={closeMobileMenu}
				>
					<TrendingUp class="h-4.5 w-4.5" />
					Finances
				</a>
				<a
					href="/bilans"
					class="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors {isActive('/bilans')
						? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white'
						: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
					onclick={closeMobileMenu}
				>
					<FileSpreadsheet class="h-4.5 w-4.5" />
					Bilans
				</a>

				<!-- SCI Switcher in mobile -->
				<div class="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800">
					<p class="mb-1 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Mes SCI</p>
					{#if scis.length === 0}
						<p class="px-3 py-2 text-xs text-slate-400 italic">Aucune SCI</p>
					{/if}
					{#each scis as sci (sci.id)}
						<a
							href={`/scis/${sci.id}`}
							class="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors {String(sci.id) === String(activeSciId)
								? 'bg-blue-50 font-medium text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
								: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
							onclick={closeMobileMenu}
						>
							<Building2 class="h-4 w-4 flex-shrink-0 {String(sci.id) === String(activeSciId) ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400'}" />
							<span class="flex-1 truncate">{sci.nom}</span>
							{#if String(sci.id) === String(activeSciId)}
								<Check class="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
							{/if}
						</a>
					{/each}
					<a
						href="/scis"
						class="flex items-center gap-2 px-3 py-2 text-xs font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-300"
						onclick={closeMobileMenu}
					>
						Voir toutes les SCI
					</a>
				</div>

				<!-- SCI sub-nav (when a SCI is active) -->
				{#if activeSciId}
					<div class="mt-2 border-t border-slate-100 pt-3 dark:border-slate-800">
						<p class="mb-1 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">{activeSci?.nom ?? 'SCI'}</p>
						{#each sciSubNav as subItem (subItem.suffix)}
							{@const href = `/scis/${activeSciId}${subItem.suffix}`}
							{@const active = subItem.suffix === '' ? isExactActive(href) : isActive(href)}
							<a
								{href}
								class="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors {active
									? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
									: 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}"
								onclick={closeMobileMenu}
							>
								<subItem.icon class="h-4 w-4" />
								{subItem.label}
							</a>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Drawer footer: account + theme -->
			<div class="border-t border-slate-200 px-3 py-3 dark:border-slate-800">
				<div class="mb-2 flex items-center justify-between px-2">
					<span class="truncate text-xs text-slate-500 dark:text-slate-400">{user?.email ?? ''}</span>
					<ThemeToggle />
				</div>
				<a
					href="/settings"
					class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
					onclick={closeMobileMenu}
				>
					<Settings class="h-4 w-4" />
					Paramètres
				</a>
				{#if loggingOut}
					<span class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-500 dark:text-slate-400">
						<LogOut class="h-4 w-4 animate-pulse" />
						Déconnexion en cours…
					</span>
				{:else}
					<button
						type="button"
						onclick={() => { closeMobileMenu(); handleLogout(); }}
						class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
					>
						<LogOut class="h-4 w-4" />
						Déconnexion
					</button>
				{/if}
			</div>
		</div>
	{/if}

	<!-- SCI Sub-nav + Breadcrumbs (merged into single bar when SCI is active) -->
	{#if activeSciId}
		<div class="border-t border-slate-100 dark:border-slate-800">
			<div class="mx-auto flex w-full max-w-7xl items-center justify-between gap-2 overflow-x-auto px-4 md:px-8">
				<!-- SCI tabs -->
				<div class="flex items-center gap-0.5">
					{#each sciSubNav as subItem (subItem.suffix)}
						{@const href = `/scis/${activeSciId}${subItem.suffix}`}
						{@const active = subItem.suffix === '' ? isExactActive(href) : isActive(href)}
						<a
							{href}
							class="relative flex items-center gap-2 whitespace-nowrap px-3.5 py-3 text-sm font-medium transition-colors {active
								? 'text-blue-600 dark:text-blue-400'
								: 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'}"
						>
							<subItem.icon class="h-4 w-4" />
							<span>{subItem.label}</span>
							{#if active}
								<span class="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-blue-600 dark:bg-blue-400"></span>
							{/if}
						</a>
					{/each}
				</div>
				<!-- Inline breadcrumbs (right side) -->
				{#if breadcrumbs.length > 2}
					<nav aria-label="Fil d'Ariane" class="hidden items-center md:flex">
						<ol class="flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500">
							{#each breadcrumbs.slice(2) as crumb, index (crumb.href)}
								{#if index > 0}
									<li><ChevronRight class="h-3 w-3 text-slate-300 dark:text-slate-600" /></li>
								{/if}
								<li>
									{#if index === breadcrumbs.slice(2).length - 1}
										<span class="truncate font-medium text-slate-600 dark:text-slate-300">{crumb.label}</span>
									{:else}
										<a
											href={crumb.href}
											class="truncate rounded px-1 py-0.5 transition-colors hover:text-slate-700 dark:hover:text-slate-200"
										>
											{crumb.label}
										</a>
									{/if}
								</li>
							{/each}
						</ol>
					</nav>
				{/if}
			</div>
		</div>
	{:else if breadcrumbs.length > 0}
		<!-- Standalone breadcrumbs (no SCI context) -->
		<div class="border-t border-slate-100 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-900/40">
			<nav
				aria-label="Fil d'Ariane"
				class="mx-auto flex w-full max-w-7xl items-center px-4 py-1.5 md:px-8"
			>
				<ol class="flex min-w-0 flex-wrap items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400">
					<li class="flex items-center gap-1">
						<a
							href="/dashboard"
							class="inline-flex items-center gap-1 rounded px-1.5 py-0.5 transition-colors hover:bg-slate-200/60 hover:text-slate-700 dark:hover:bg-slate-700 dark:hover:text-slate-200"
						>
							<House class="h-3.5 w-3.5" />
						</a>
					</li>
					{#each breadcrumbs as crumb, index (crumb.href)}
						<li class="flex items-center gap-1">
							<ChevronRight class="h-3.5 w-3.5 shrink-0 text-slate-300 dark:text-slate-600" />
							{#if index === breadcrumbs.length - 1}
								<span class="truncate font-medium text-slate-700 dark:text-slate-200">{crumb.label}</span>
							{:else}
								<a
									href={crumb.href}
									class="truncate rounded px-1.5 py-0.5 transition-colors hover:bg-slate-200/60 hover:text-slate-700 dark:hover:bg-slate-700 dark:hover:text-slate-200"
								>
									{crumb.label}
								</a>
							{/if}
						</li>
					{/each}
				</ol>
			</nav>
		</div>
	{/if}
</nav>

<style>
	@keyframes slideInLeft {
		from {
			transform: translateX(-100%);
		}
		to {
			transform: translateX(0);
		}
	}
</style>
