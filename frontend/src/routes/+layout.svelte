<script lang="ts">
	import { onMount } from 'svelte';
	import type { User } from '@supabase/supabase-js';
	import { page } from '$app/state';
	import { Menu, X, Search } from 'lucide-svelte';
	import { supabase } from '$lib/supabase';
	import {
		clearFakeSession,
		getCurrentSession,
		subscribeToSessionChanges
	} from '$lib/auth/session';
	import { Button } from '$lib/components/ui/button';
	import { Toaster } from '$lib/components/ui/toast';
	import AppBreadcrumbs from '$lib/components/AppBreadcrumbs.svelte';
	import AppSidebar from '$lib/components/AppSidebar.svelte';
	import { theme } from '$lib/stores/theme';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import CookieConsent from '$lib/components/CookieConsent.svelte';
	import NotificationCenter from '$lib/components/NotificationCenter.svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
	let user = $state<User | null>(null);
	let mobileMenuOpen = $state(false);
	let accountMenuOpen = $state(false);
	let previousPath = page.url.pathname;
	let accountMenuContainer = $state<HTMLDivElement | null>(null);

	const authenticatedNavItems = [
		{ href: '/dashboard', label: 'Cockpit' },
		{ href: '/scis', label: 'SCI' },
		{ href: '/biens', label: 'Biens' },
		{ href: '/loyers', label: 'Loyers' },
		{ href: '/pricing', label: 'Tarifs' }
	];

	const authenticatedUtilityItems = [
		{ href: '/account', label: 'Compte' },
		{ href: '/settings', label: 'Paramètres' },
		{ href: '/account/privacy', label: 'Confidentialité' }
	];

	const isAppRoute = $derived(
		user &&
			page.url.pathname !== '/' &&
			page.url.pathname !== '/login' &&
			page.url.pathname !== '/register' &&
			page.url.pathname !== '/privacy' &&
			!page.url.pathname.startsWith('/auth')
	);

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
			}
		});

		const subscription = subscribeToSessionChanges((session) => {
			if (mounted) {
				user = session?.user || null;
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
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div
	class="min-h-screen bg-white text-slate-900 transition-colors dark:bg-slate-950 dark:text-slate-50"
>
	{#if isAppRoute}
		<!-- Authenticated layout: slim top bar + sidebar + content -->
		<div class="flex h-screen overflow-hidden">
			<AppSidebar {user} />

			<div class="flex flex-1 flex-col overflow-hidden">
				<!-- Slim top bar for authenticated users -->
				<header
					class="flex h-14 flex-shrink-0 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/95"
				>
					<div class="flex items-center gap-3">
						<Button
							type="button"
							variant="ghost"
							size="icon"
							class="md:hidden"
							aria-expanded={mobileMenuOpen}
							aria-label={mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
							onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
						>
							{#if mobileMenuOpen}
								<X class="h-4 w-4" />
							{:else}
								<Menu class="h-4 w-4" />
							{/if}
						</Button>
						<a
							href="/dashboard"
							class="text-lg font-bold tracking-tight text-slate-900 md:hidden dark:text-slate-100"
						>
							GererSCI
						</a>
						<AppBreadcrumbs />
					</div>

					<div class="flex items-center gap-2">
						<NotificationCenter />
						<ThemeToggle />

						<div class="relative hidden md:block" bind:this={accountMenuContainer}>
							<button
								type="button"
								class="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-2 py-1.5 text-sm transition-colors hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700 dark:hover:bg-slate-900"
								aria-haspopup="menu"
								aria-expanded={accountMenuOpen}
								aria-controls="desktop-account-menu"
								onkeydown={(event) => {
									if (event.key === 'Escape') accountMenuOpen = false;
								}}
								onclick={() => (accountMenuOpen = !accountMenuOpen)}
							>
								<span
									class="hidden max-w-[10rem] truncate text-xs text-slate-600 lg:block dark:text-slate-300"
								>
									{user?.email}
								</span>
								<span
									class="rounded-full bg-slate-900 px-2.5 py-0.5 text-[11px] font-semibold text-white dark:bg-slate-100 dark:text-slate-950"
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
									class="absolute top-full right-0 mt-2 w-64 rounded-2xl border border-slate-200 bg-white p-2 shadow-lg dark:border-slate-800 dark:bg-slate-950"
									onkeydown={(event) => {
										if (event.key === 'Escape') accountMenuOpen = false;
									}}
								>
									<div
										class="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900"
									>
										<p class="text-[0.65rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
											Connecté
										</p>
										<p class="mt-1 truncate text-sm font-medium text-slate-900 dark:text-slate-100">
											{user?.email}
										</p>
									</div>

									<div class="mt-2 grid gap-1">
										{#each authenticatedUtilityItems as item (item.href)}
											<a
												href={item.href}
												role="menuitem"
												class="rounded-xl px-3 py-2 text-sm font-medium transition-colors {isActivePath(item.href)
													? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
													: 'text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800'}"
												onclick={() => (accountMenuOpen = false)}
											>
												{item.label}
											</a>
										{/each}
									</div>

									<Button variant="outline" size="sm" class="mt-2 w-full" onclick={handleLogout}>
										Déconnexion
									</Button>
								</div>
							{/if}
						</div>
					</div>
				</header>

				<!-- Mobile menu overlay -->
				{#if mobileMenuOpen}
					<div
						class="absolute inset-0 z-40 bg-white md:hidden dark:bg-slate-950"
					>
						<div class="p-4">
							<div class="mb-4 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
								<p class="text-[0.65rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Session active</p>
								<p class="mt-1 truncate text-sm font-medium text-slate-900 dark:text-slate-100">{user?.email}</p>
							</div>

							<p class="mb-2 text-[0.6rem] font-semibold tracking-[0.2em] text-slate-500 uppercase">Pilotage</p>
							<div class="grid gap-1">
								{#each authenticatedNavItems as item (item.href)}
									<a
										href={item.href}
										class="rounded-xl px-3 py-2.5 text-sm font-medium transition-colors {isActivePath(item.href)
											? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
											: 'text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800'}"
									>
										{item.label}
									</a>
								{/each}
							</div>

							<p class="mt-4 mb-2 text-[0.6rem] font-semibold tracking-[0.2em] text-slate-500 uppercase">Compte</p>
							<div class="grid gap-1">
								{#each authenticatedUtilityItems as item (item.href)}
									<a
										href={item.href}
										class="rounded-xl px-3 py-2.5 text-sm font-medium transition-colors {isActivePath(item.href)
											? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950'
											: 'text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800'}"
									>
										{item.label}
									</a>
								{/each}
								<Button variant="outline" size="sm" class="mt-2" onclick={handleLogout}>
									Déconnexion
								</Button>
							</div>
						</div>
					</div>
				{/if}

				<!-- Main content area with scroll -->
				<main class="flex-1 overflow-y-auto">
					{@render children()}
				</main>
			</div>
		</div>
	{:else}
		<!-- Public layout: traditional top nav -->
		<nav
			class="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/95"
		>
			<div class="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-4 md:px-8">
				<div class="flex items-center gap-3">
					<a
						href="/"
						class="text-xl font-bold tracking-tight text-slate-900 transition-colors hover:text-blue-600 dark:text-slate-100 dark:hover:text-blue-400"
					>
						GererSCI
					</a>
				</div>

				<div class="flex items-center gap-2 md:gap-4">
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
					<ThemeToggle />
				</div>
			</div>
		</nav>

		{@render children()}
	{/if}

	<!-- Footer -->
	<footer class="border-t border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
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
						{#if user}
							<li>
								<a
									href="/pricing"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Tarifs</a>
							</li>
							<li>
								<a
									href="/dashboard"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Cockpit</a>
							</li>
							<li>
								<a
									href="/scis"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Portefeuille SCI</a>
							</li>
						{:else}
							<li>
								<a
									href="/pricing"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Tarifs</a>
							</li>
							<li>
								<a
									href="/#features"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Fonctionnalités</a>
							</li>
							<li>
								<a
									href="/#studies"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Études & sources</a>
							</li>
						{/if}
					</ul>
				</div>

				<div class="space-y-4">
					<h4 class="font-medium text-slate-900 dark:text-slate-100">
						{user ? 'Compte' : 'Support'}
					</h4>
					<ul class="space-y-2 text-sm">
						{#if user}
							<li>
								<a href="/account" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Compte</a>
							</li>
							<li>
								<a href="/settings" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Paramètres</a>
							</li>
							<li>
								<a href="/account/privacy" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Confidentialité</a>
							</li>
						{:else}
							<li>
								<a href="/login" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Connexion</a>
							</li>
							<li>
								<a href="/register" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Inscription</a>
							</li>
							<li>
								<a href="/privacy" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Confidentialité</a>
							</li>
						{/if}
					</ul>
				</div>

				<div class="space-y-4">
					<h4 class="font-medium text-slate-900 dark:text-slate-100">
						{user ? 'Pilotage' : 'Entreprise'}
					</h4>
					<ul class="space-y-2 text-sm">
						<li>
							<a href="/dashboard" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">
								{user ? 'Cockpit' : 'Tableau de bord'}
							</a>
						</li>
						<li>
							<a href="/biens" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Gestion des biens</a>
						</li>
						<li>
							<a href="/loyers" class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">Suivi des loyers</a>
						</li>
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
	</footer>

	{#if user}
		<CommandPalette />
	{/if}
	<Toaster />
	<CookieConsent />
</div>
