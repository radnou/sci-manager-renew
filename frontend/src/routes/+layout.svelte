<script lang="ts">
	import { onMount } from 'svelte';
	import type { User } from '@supabase/supabase-js';
	import { page } from '$app/state';
	import { Menu, X } from 'lucide-svelte';
	import { supabase } from '$lib/supabase';
	import { clearFakeSession, getCurrentSession, subscribeToSessionChanges } from '$lib/auth/session';
	import { Button } from '$lib/components/ui/button';
	import { Toaster } from '$lib/components/ui/toast';
	import AppBreadcrumbs from '$lib/components/AppBreadcrumbs.svelte';
	import { theme } from '$lib/stores/theme';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import CookieConsent from '$lib/components/CookieConsent.svelte';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
	let user = $state<User | null>(null);
	let mobileMenuOpen = $state(false);
	let previousPath = page.url.pathname;

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

	function isActivePath(href: string) {
		return page.url.pathname === href || (href !== '/' && page.url.pathname.startsWith(`${href}/`));
	}

	onMount(() => {
		let mounted = true;

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

		return () => {
			mounted = false;
			subscription.unsubscribe();
		};
	});

	async function handleLogout() {
		await supabase.auth.signOut();
		clearFakeSession();
		user = null;
	}

	$effect(() => {
		const currentPath = page.url.pathname;
		if (currentPath !== previousPath) {
			mobileMenuOpen = false;
			previousPath = currentPath;
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
					<span class="hidden rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold tracking-[0.16em] text-slate-600 uppercase lg:inline-flex dark:bg-slate-800 dark:text-slate-300">
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

					<div class="hidden items-center gap-2 xl:flex">
						{#each authenticatedUtilityItems as item (item.href)}
							<a
								href={item.href}
								aria-current={isActivePath(item.href) ? 'page' : undefined}
								class={`rounded-full px-3 py-2 text-sm font-medium transition-colors ${
									isActivePath(item.href)
										? 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100'
										: 'text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100'
								}`}
							>
								{item.label}
							</a>
						{/each}
					</div>

					<div class="hidden items-center gap-3 sm:flex">
						<span class="max-w-[14rem] truncate text-sm text-slate-600 dark:text-slate-400">
							{user.email}
						</span>
						<Button variant="outline" size="sm" onclick={handleLogout}>Déconnexion</Button>
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
				<div class="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Session active
					</p>
					<p class="mt-1 truncate text-sm font-medium text-slate-900 dark:text-slate-100">{user.email}</p>
				</div>

				<div class="grid gap-2">
					<p class="mt-1 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Pilotage</p>
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

					<p class="mt-4 text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Compte</p>
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
					<Button variant="outline" size="sm" class="mt-2" onclick={handleLogout}>Déconnexion</Button>
				</div>
			</div>
		{/if}
	</nav>

	{#if page.url.pathname !== '/'}
		<AppBreadcrumbs />
	{/if}

	{@render children()}

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
						<li>
							<a
								href="/pricing"
								class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Tarifs</a
							>
						</li>
						<li>
							<a
								href="/#features"
								class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Fonctionnalités</a
							>
						</li>
						<li>
							<a
								href="/#studies"
								class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Études & sources</a
							>
						</li>
					</ul>
				</div>

				<div class="space-y-4">
					<h4 class="font-medium text-slate-900 dark:text-slate-100">Support</h4>
					<ul class="space-y-2 text-sm">
						<li>
							<a
								href="/login"
								class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Connexion</a
							>
						</li>
						<li>
							<a
								href="/register"
								class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Inscription</a
							>
						</li>
						<li>
							<a
								href="/privacy"
								class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Confidentialité</a
							>
						</li>
					</ul>
				</div>

				<div class="space-y-4">
					<h4 class="font-medium text-slate-900 dark:text-slate-100">Entreprise</h4>
					<ul class="space-y-2 text-sm">
						<li>
							<a
								href="/dashboard"
								class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Tableau de bord</a
							>
						</li>
						<li>
							<a
								href="/biens"
								class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Gestion des biens</a
							>
						</li>
						<li>
							<a
								href="/loyers"
								class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								>Suivi des loyers</a
							>
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

	<Toaster />
	<CookieConsent />
</div>
