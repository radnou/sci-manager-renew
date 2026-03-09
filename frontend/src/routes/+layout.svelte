<script lang="ts">
	import { onMount } from 'svelte';
	import type { User } from '@supabase/supabase-js';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { Menu, X, Search } from 'lucide-svelte';
	import { supabase } from '$lib/supabase';
	import {
		clearFakeSession,
		getCurrentSession,
		subscribeToSessionChanges
	} from '$lib/auth/session';
	import { buildLoginRedirect, isGuestOnlyRoute, isProtectedRoute } from '$lib/auth/route-guard';
	import { Button } from '$lib/components/ui/button';
	import { Toaster } from '$lib/components/ui/toast';
	import AppBreadcrumbs from '$lib/components/AppBreadcrumbs.svelte';
	import { theme } from '$lib/stores/theme';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import CookieConsent from '$lib/components/CookieConsent.svelte';
	import AppSidebar from '$lib/components/AppSidebar.svelte';
	import NotificationCenter from '$lib/components/NotificationCenter.svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
	let user = $state<User | null>(null);
	let authResolved = $state(false);
	let mobileMenuOpen = $state(false);
	let accountMenuOpen = $state(false);
	let previousPath = page.url.pathname;
	let accountMenuContainer = $state<HTMLDivElement | null>(null);

	const authenticatedNavItems = [
		{ href: '/dashboard', label: 'Cockpit' },
		{ href: '/scis', label: 'Portefeuille' },
		{ href: '/exploitation', label: 'Exploitation' },
		{ href: '/finance', label: 'Finance' }
	];

	const authenticatedUtilityItems = [
		{ href: '/account', label: 'Compte' },
		{ href: '/pricing', label: 'Offre et facturation' },
		{ href: '/settings', label: 'Paramètres' },
		{ href: '/account/privacy', label: 'Confidentialité' }
	];

	function isActivePath(href: string) {
		return page.url.pathname === href || (href !== '/' && page.url.pathname.startsWith(`${href}/`));
	}

	onMount(() => {
		let mounted = true;
		const handleDocumentClick = (event: MouseEvent) => {
			if (accountMenuContainer && !accountMenuContainer.contains(event.target as Node)) {
				accountMenuOpen = false;
			}
		};

		// Initialize theme
		theme.initialize();

		getCurrentSession().then((session) => {
			if (mounted) {
				user = session?.user || null;
				authResolved = true;
			}
		});

		const subscription = subscribeToSessionChanges((session) => {
			if (mounted) {
				user = session?.user || null;
				authResolved = true;
			}
		});

		document.addEventListener('mousedown', handleDocumentClick);

		return () => {
			mounted = false;
			subscription.unsubscribe();
			document.removeEventListener('mousedown', handleDocumentClick);
		};
	});

	async function handleLogout() {
		await supabase.auth.signOut();
		clearFakeSession();
		user = null;
		accountMenuOpen = false;
		mobileMenuOpen = false;
	}

	$effect(() => {
		const currentPath = page.url.pathname;
		if (currentPath !== previousPath) {
			mobileMenuOpen = false;
			accountMenuOpen = false;
			previousPath = currentPath;
		}
	});

	$effect(() => {
		if (!authResolved) {
			return;
		}

		const pathname = page.url.pathname;
		const search = page.url.search;

		if (!user && isProtectedRoute(pathname)) {
			goto(buildLoginRedirect(pathname, search), { replaceState: true, noScroll: true });
			return;
		}

		if (user && pathname === '/') {
			goto('/dashboard', { replaceState: true, noScroll: true });
			return;
		}

		if (user && isGuestOnlyRoute(pathname)) {
			goto('/dashboard', { replaceState: true, noScroll: true });
		}
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div
	class="min-h-screen bg-white text-slate-900 transition-colors dark:bg-slate-950 dark:text-slate-50"
>
	<nav
		class="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/95"
	>
		<div class="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-4 md:px-8">
			<div class="flex items-center gap-3">
				<a
					href={user ? '/dashboard' : '/'}
					class="text-xl font-bold tracking-tight text-slate-900 transition-colors hover:text-blue-600 dark:text-slate-100 dark:hover:text-blue-400"
				>
					GererSCI
				</a>
				{#if user}
					<span
						class="hidden rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold tracking-[0.16em] text-slate-600 uppercase lg:inline-flex dark:bg-slate-800 dark:text-slate-300"
					>
						Espace de pilotage
					</span>
				{/if}
			</div>

			<div class="flex items-center gap-2 md:gap-4">
				{#if user}
					<div class="hidden items-center gap-2 md:flex">
						{#each authenticatedNavItems as item (item.href)}
							<a
								href={item.href}
								aria-current={isActivePath(item.href) ? 'page' : undefined}
								class={`rounded-full px-3 py-2 text-sm font-medium transition-colors ${
									isActivePath(item.href)
										? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
										: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100'
								}`}
							>
								{item.label}
							</a>
						{/each}
					</div>

					<NotificationCenter />

					<div class="relative hidden md:block" bind:this={accountMenuContainer}>
						<button
							type="button"
							class="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-2 py-2 text-sm transition-colors hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700 dark:hover:bg-slate-900"
							aria-haspopup="menu"
							aria-expanded={accountMenuOpen}
							aria-controls="desktop-account-menu"
							onkeydown={(event) => {
								if (event.key === 'Escape') {
									accountMenuOpen = false;
								}
							}}
							onclick={() => {
								accountMenuOpen = !accountMenuOpen;
							}}
						>
							<span
								class="hidden max-w-[12rem] truncate text-slate-600 lg:block dark:text-slate-300"
								>{user.email}</span
							>
							<span
								class="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white dark:bg-slate-100 dark:text-slate-950"
							>
								Compte
							</span>
						</button>

						{#if accountMenuOpen}
							<div
								id="desktop-account-menu"
								role="menu"
								aria-label="Menu du compte"
								tabindex="-1"
								class="absolute top-full right-0 mt-3 w-72 rounded-[1.5rem] border border-slate-200 bg-white p-3 shadow-[0_20px_50px_-28px_rgba(15,23,42,0.45)] dark:border-slate-800 dark:bg-slate-950"
								onkeydown={(event) => {
									if (event.key === 'Escape') {
										accountMenuOpen = false;
									}
								}}
							>
								<div
									class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900"
								>
									<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
										Espace opérateur
									</p>
									<p class="mt-1 truncate text-sm font-medium text-slate-900 dark:text-slate-100">
										{user.email}
									</p>
								</div>

								<div class="mt-3 grid gap-2">
									{#each authenticatedUtilityItems as item (item.href)}
										<a
											href={item.href}
											role="menuitem"
											aria-current={isActivePath(item.href) ? 'page' : undefined}
											class={`rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${
												isActivePath(item.href)
													? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
													: 'bg-slate-50 text-slate-700 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800'
											}`}
											onclick={() => {
												accountMenuOpen = false;
											}}
										>
											{item.label}
										</a>
									{/each}
								</div>

								<Button variant="outline" size="sm" class="mt-3 w-full" onclick={handleLogout}
									>Déconnexion</Button
								>
							</div>
						{/if}
					</div>

					<Button
						type="button"
						variant="outline"
						size="icon"
						class="md:hidden"
						aria-expanded={mobileMenuOpen}
						aria-controls="mobile-navigation"
						aria-label={mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
						onclick={() => {
							mobileMenuOpen = !mobileMenuOpen;
						}}
					>
						{#if mobileMenuOpen}
							<X class="h-4 w-4" />
						{:else}
							<Menu class="h-4 w-4" />
						{/if}
					</Button>
				{:else}
					<div class="hidden items-center gap-4 md:flex">
						<a
							href="/pricing"
							class="text-sm font-medium text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
						>
							Tarifs
						</a>
					</div>
					<div class="flex items-center gap-3">
						<a href="/login">
							<Button variant="ghost" size="sm">Connexion</Button>
						</a>
						<a href="/register">
							<Button
								size="sm"
								class="border-0 bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:from-blue-600 hover:to-cyan-600"
							>
								Inscription
							</Button>
						</a>
					</div>
				{/if}

				<ThemeToggle />
			</div>
		</div>

		{#if user && mobileMenuOpen}
			<div
				id="mobile-navigation"
				class="border-t border-slate-200 bg-white px-4 py-4 md:hidden dark:border-slate-800 dark:bg-slate-950"
			>
				<div
					class="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900"
				>
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Session active
					</p>
					<p class="mt-1 truncate text-sm font-medium text-slate-900 dark:text-slate-100">
						{user.email}
					</p>
				</div>

				<div class="grid gap-2">
					<p class="mt-1 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Pilotage
					</p>
					{#each authenticatedNavItems as item (item.href)}
						<a
							href={item.href}
							aria-current={isActivePath(item.href) ? 'page' : undefined}
							class={`rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${
								isActivePath(item.href)
									? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
									: 'bg-slate-50 text-slate-700 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800'
							}`}
						>
							{item.label}
						</a>
					{/each}

					<p class="mt-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Compte
					</p>
					{#each authenticatedUtilityItems as item (item.href)}
						<a
							href={item.href}
							aria-current={isActivePath(item.href) ? 'page' : undefined}
							class={`rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${
								isActivePath(item.href)
									? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
									: 'bg-slate-50 text-slate-700 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800'
							}`}
						>
							{item.label}
						</a>
					{/each}
					<Button variant="outline" size="sm" class="mt-2" onclick={handleLogout}
						>Déconnexion</Button
					>
				</div>
			</div>
		{/if}
	</nav>

	{#if page.url.pathname !== '/'}
		<AppBreadcrumbs />
	{/if}

	{#if authResolved && user && page.url.pathname === '/'}
		<section class="mx-auto w-full max-w-7xl px-4 py-8 md:px-8">
			<div
				class="rounded-[2rem] border border-slate-200 bg-white px-6 py-12 text-center shadow-[0_30px_80px_-48px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-950"
			>
				<p class="text-sm font-semibold tracking-[0.18em] text-slate-500 uppercase">
					Espace connecté
				</p>
				<h1 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">
					Ouverture du cockpit
				</h1>
				<p class="mt-3 text-sm text-slate-600 dark:text-slate-400">
					Redirection vers votre dashboard opérateur.
				</p>
			</div>
		</section>
	{:else if isProtectedRoute(page.url.pathname) && (!authResolved || !user)}
		<section class="mx-auto w-full max-w-7xl px-4 py-8 md:px-8">
			<div
				class="rounded-[2rem] border border-slate-200 bg-white px-6 py-12 text-center shadow-[0_30px_80px_-48px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-950"
			>
				<p class="text-sm font-semibold tracking-[0.18em] text-slate-500 uppercase">
					Zone protégée
				</p>
				<h1 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">
					Connexion requise
				</h1>
				<p class="mt-3 text-sm text-slate-600 dark:text-slate-400">
					Redirection vers l’espace de connexion sécurisé.
				</p>
			</div>
		</section>
	{:else if user}
		<div class="flex">
			<AppSidebar {user} />
			<main class="flex-1 overflow-y-auto">
				{@render children()}
			</main>
		</div>
	{:else}
		<main class="flex-1 overflow-y-auto">
			{@render children()}
		</main>
	{/if}

	{#if user}
		<CommandPalette />
	{/if}

	<!-- Footer -->
	<footer class="border-t border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
		{#if user}
			<div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
				<div class="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
					<div class="space-y-2">
						<h3 class="font-semibold text-slate-900 dark:text-slate-100">Environnement opérateur</h3>
						<p class="max-w-2xl text-sm text-slate-600 dark:text-slate-400">
							Shell connecté recentré sur le portefeuille, l’exploitation, la finance et le cadrage du compte.
						</p>
					</div>

					<div class="flex flex-wrap gap-2">
						<a href="/dashboard" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:border-slate-300 hover:text-slate-900 dark:border-slate-800 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-slate-100">Cockpit</a>
						<a href="/scis" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:border-slate-300 hover:text-slate-900 dark:border-slate-800 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-slate-100">Portefeuille</a>
						<a href="/account" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:border-slate-300 hover:text-slate-900 dark:border-slate-800 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-slate-100">Compte</a>
						<a href="/account/privacy" class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:border-slate-300 hover:text-slate-900 dark:border-slate-800 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-slate-100">Confidentialité</a>
					</div>
				</div>

				<div class="mt-5 border-t border-slate-200 pt-5 dark:border-slate-800">
					<div class="flex flex-col items-center justify-between gap-4 sm:flex-row">
						<p class="text-sm text-slate-600 dark:text-slate-400">
							© 2026 GererSCI. Tous droits réservés.
						</p>
						<div class="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
							<span>🇫🇷 Fait en France</span>
							<span>•</span>
							<span>Conforme RGPD</span>
						</div>
					</div>
				</div>
			</div>
		{:else}
			<div class="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
				<div class="grid gap-8 md:grid-cols-4">
					<div class="space-y-4">
						<h3 class="font-semibold text-slate-900 dark:text-slate-100">GererSCI</h3>
						<p class="text-sm text-slate-600 dark:text-slate-400">
							Pilotez votre SCI comme un opérateur avec des outils professionnels.
						</p>
					</div>

					<div class="space-y-4">
						<h4 class="font-medium text-slate-900 dark:text-slate-100">Produit</h4>
						<ul class="space-y-2 text-sm">
							<li><a href="/pricing" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Tarifs</a></li>
							<li><a href="/#features" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Fonctionnalités</a></li>
							<li><a href="/#studies" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Études & sources</a></li>
						</ul>
					</div>

					<div class="space-y-4">
						<h4 class="font-medium text-slate-900 dark:text-slate-100">Support</h4>
						<ul class="space-y-2 text-sm">
							<li><a href="/login" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Connexion</a></li>
							<li><a href="/register" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Inscription</a></li>
							<li><a href="/privacy" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Confidentialité</a></li>
						</ul>
					</div>

					<div class="space-y-4">
						<h4 class="font-medium text-slate-900 dark:text-slate-100">Entreprise</h4>
						<ul class="space-y-2 text-sm">
							<li><a href="/dashboard" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Tableau de bord</a></li>
							<li><a href="/biens" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Gestion des biens</a></li>
							<li><a href="/loyers" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Suivi des loyers</a></li>
						</ul>
					</div>
				</div>

				<div class="mt-8 border-t border-slate-200 pt-8 dark:border-slate-800">
					<div class="flex flex-col items-center justify-between gap-4 sm:flex-row">
						<p class="text-sm text-slate-600 dark:text-slate-400">
							© 2026 GererSCI. Tous droits réservés.
						</p>
						<div class="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
							<span>🇫🇷 Fait en France</span>
							<span>•</span>
							<span>Conforme RGPD</span>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</footer>

	<Toaster />
	<CookieConsent />
</div>
