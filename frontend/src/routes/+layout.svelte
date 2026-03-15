<script lang="ts">
	import { onMount } from 'svelte';
	import { afterNavigate } from '$app/navigation';
	import type { User } from '@supabase/supabase-js';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { Menu, X } from 'lucide-svelte';
	import { initMatomo, trackPageView } from '$lib/matomo';
	import { supabase } from '$lib/supabase';
	import {
		clearFakeSession,
		getCurrentSession,
		subscribeToSessionChanges
	} from '$lib/auth/session';
	import {
		buildLoginRedirect,
		isGuestOnlyRoute,
		isProtectedRoute,
		isPublicRoute
	} from '$lib/auth/route-guard';
	import { Button } from '$lib/components/ui/button';
	import { Toaster } from '$lib/components/ui/toast';
	import { theme } from '$lib/stores/theme';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import CookieConsent from '$lib/components/CookieConsent.svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
	let user = $state<User | null>(null);
	let authResolved = $state(false);
	let mobileMenuOpen = $state(false);
	let previousPath = page.url.pathname;

	// Track page views on SvelteKit client-side navigation
	afterNavigate(() => {
		trackPageView(page.url.pathname);
	});

	onMount(() => {
		let mounted = true;

		// Initialize theme
		theme.initialize();

		// Initialize Matomo analytics
		initMatomo();

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

		return () => {
			mounted = false;
			subscription.unsubscribe();
		};
	});

	async function handleLogout() {
		await supabase.auth.signOut();
		clearFakeSession();
		user = null;
		mobileMenuOpen = false;
		goto('/login', { replaceState: true });
	}

	$effect(() => {
		const currentPath = page.url.pathname;
		if (currentPath !== previousPath) {
			mobileMenuOpen = false;
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

	// Show public navbar only for non-authenticated or public routes
	const showPublicNav = $derived(!user || isPublicRoute(page.url.pathname));
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div
	class="min-h-screen bg-white text-slate-900 transition-colors dark:bg-slate-950 dark:text-slate-50"
>
	<!-- Skip to content link for keyboard / screen reader users -->
	<a
		href="#main-content"
		class="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-blue-600 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white focus:shadow-lg focus:outline-none"
	>
		Aller au contenu principal
	</a>

	<!-- Public navbar: only for visitors / public pages -->
	{#if showPublicNav && !isProtectedRoute(page.url.pathname)}
		<nav
			aria-label="Navigation principale"
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
						<a
							href="/simulateur-cerfa"
							class="text-sm font-medium text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
						>
							Simulateur
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

			{#if mobileMenuOpen}
				<div
					id="mobile-navigation"
					class="border-t border-slate-200 bg-white px-4 py-4 md:hidden dark:border-slate-800 dark:bg-slate-950"
				>
					<div class="grid gap-2">
						<a
							href="/pricing"
							class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Tarifs
						</a>
						<a
							href="/simulateur-cerfa"
							class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Simulateur
						</a>
						<a
							href="/login"
							class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Connexion
						</a>
					</div>
				</div>
			{/if}
		</nav>
	{/if}

	{#if isPublicRoute(page.url.pathname) && !user}
		<div id="main-content">{@render children()}</div>
	{:else if authResolved && user && page.url.pathname === '/'}
		<section class="flex min-h-[60vh] items-center justify-center">
			<p class="animate-pulse text-sm text-slate-500">Redirection vers le tableau de bord…</p>
		</section>
	{:else if isProtectedRoute(page.url.pathname) && (!authResolved || !user)}
		<section class="mx-auto w-full max-w-7xl px-4 py-8 md:px-8">
			<div
				class="rounded-[2rem] border border-slate-200 bg-white px-6 py-12 text-center shadow-[0_30px_80px_-48px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-950"
			>
				<p class="text-sm font-semibold tracking-[0.15em] text-slate-500 uppercase">
					Zone protégée
				</p>
				<h1 class="mt-3 text-2xl font-semibold text-slate-900 dark:text-slate-100">
					Connexion requise
				</h1>
				<p class="mt-3 text-sm text-slate-600 dark:text-slate-400">
					Redirection vers l'espace de connexion sécurisé.
				</p>
			</div>
		</section>
	{:else if authResolved}
		<div id="main-content">{@render children()}</div>
	{/if}

	<!-- Footer: only for public pages -->
	{#if !user || isPublicRoute(page.url.pathname)}
		<footer aria-label="Pied de page" class="border-t border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
			<div class="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
				<div class="grid gap-8 md:grid-cols-4">
					<div class="space-y-4">
						<h3 class="font-semibold text-slate-900 dark:text-slate-100">GererSCI</h3>
						<p class="text-sm text-slate-600 dark:text-slate-400">
							Plateforme de gestion et d'intelligence fiscale pour SCI.
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
									href="/simulateur-cerfa"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
									>Simulateur CERFA 2044</a
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
									href="/confidentialite"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
									>Confidentialité</a
								>
							</li>
							<li>
								<a
									href="/mentions-legales"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
									>Mentions légales</a
								>
							</li>
							<li>
								<a
									href="/cgu"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
									>CGU</a
								>
							</li>
							<li>
								<a
									href="/cgv"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
									>CGV</a
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
									href="/scis"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
									>Mes SCI</a
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
							<a href="/mentions-legales" class="transition-colors hover:text-slate-900 dark:hover:text-slate-100">Mentions légales</a>
							<span>•</span>
							<a href="/confidentialite" class="transition-colors hover:text-slate-900 dark:hover:text-slate-100">Confidentialité</a>
							<span>•</span>
							<a href="/cgu" class="transition-colors hover:text-slate-900 dark:hover:text-slate-100">CGU</a>
							<span>•</span>
							<a href="/cgv" class="transition-colors hover:text-slate-900 dark:hover:text-slate-100">CGV</a>
						</div>
					</div>
				</div>
			</div>
		</footer>
	{/if}

	{#if user}
		<CommandPalette />
	{/if}

	<Toaster />
	<CookieConsent />
</div>
