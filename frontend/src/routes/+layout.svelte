<script lang="ts">
	import { onMount } from 'svelte';
	import { afterNavigate, onNavigate } from '$app/navigation';
	import type { User } from '@supabase/supabase-js';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { Menu, X } from 'lucide-svelte';
	import { initAnalytics, trackPageView, trackEvent, EVENTS } from '$lib/analytics';
	import { supabase } from '$lib/supabase';
	import {
		clearFakeSession,
		getCurrentSession,
		resetSessionResolution,
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
	import CookieBanner from '$lib/components/CookieBanner.svelte';
	import CommandPalette from '$lib/components/CommandPalette.svelte';
	import OfflineBanner from '$lib/components/OfflineBanner.svelte';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
	let user = $state<User | null>(null);
	let authResolved = $state(false);
	let mobileMenuOpen = $state(false);
	let simulateursOpen = $state(false);
	let previousPath = page.url.pathname;

	// Smooth page transitions via View Transitions API (Chrome/Edge/Safari)
	// Falls back gracefully to instant navigation in unsupported browsers
	onNavigate((navigation) => {
		// @ts-ignore - View Transitions API not yet in all TS libs
		if (!document.startViewTransition) return;
		return new Promise((resolve) => {
			// @ts-ignore
			document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
		});
	});

	// Track page views on SvelteKit client-side navigation
	afterNavigate(() => {
		trackPageView(page.url.pathname);
	});

	onMount(() => {
		let mounted = true;

		// Initialize theme
		theme.initialize();

		// Initialize analytics providers (Plausible / Matomo if configured)
		initAnalytics();

		// Reset session resolution on each page mount so that
		// getCurrentSession() will wait for INITIAL_SESSION if needed.
		resetSessionResolution();

		// Get current session first (restores from localStorage),
		// then subscribe to changes. This prevents the redirect-to-/login
		// flash on SPA navigation when the session is already stored.
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
		trackEvent(EVENTS.LOGOUT);
		await supabase.auth.signOut();
		clearFakeSession();
		user = null;
		mobileMenuOpen = false;
		// Brief visual feedback then redirect to home
		await new Promise((r) => setTimeout(r, 500));
		window.location.href = '/';
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
			const next = page.url.searchParams.get('next') || page.url.searchParams.get('redirect');
			goto(next || '/dashboard', { replaceState: true, noScroll: true });
		}
	});

	// Show public navbar only for non-authenticated or public routes
	const isAdminPage = $derived(page.url.pathname.startsWith('/admin'));
	const showPublicNav = $derived(!isAdminPage && (!user || isPublicRoute(page.url.pathname)));
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
						GérerSCI
					</a>
				</div>

				<div class="flex items-center gap-2 md:gap-4">
					<!-- Mobile hamburger button -->
					<button
						class="inline-flex items-center justify-center rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 md:hidden dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
						aria-label="Menu"
						aria-expanded={mobileMenuOpen}
						aria-controls="mobile-navigation"
						onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
					>
						{#if mobileMenuOpen}
							<X class="h-5 w-5" />
						{:else}
							<Menu class="h-5 w-5" />
						{/if}
					</button>
					<div class="hidden items-center gap-4 md:flex">
						<a
							href="/pricing"
							class="text-sm font-medium text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
						>
							Tarifs
						</a>
						<div class="relative">
							<button
								class="flex items-center gap-1 text-sm font-medium text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
								aria-haspopup="true"
								aria-expanded={simulateursOpen}
								onclick={() => (simulateursOpen = !simulateursOpen)}
								onkeydown={(e) => { if (e.key === 'Escape') simulateursOpen = false; }}
							>
								Simulateurs
								<svg class="h-3 w-3 transition-transform {simulateursOpen ? 'rotate-180' : ''}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
									<path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
								</svg>
							</button>
							{#if simulateursOpen}
							<div class="absolute left-0 top-full z-50 pt-2">
								<div class="w-56 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg dark:border-slate-700 dark:bg-slate-800">
									<a
										href="/simulateur-cerfa"
										class="block rounded-lg px-3 py-2.5 text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700"
										onclick={() => (simulateursOpen = false)}
									>
										<span class="font-medium">CERFA 2044</span>
										<span class="mt-0.5 block text-xs text-slate-500 dark:text-slate-400">Revenus fonciers</span>
									</a>
									<a
										href="/generateur-quittance"
										class="block rounded-lg px-3 py-2.5 text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700"
										onclick={() => (simulateursOpen = false)}
									>
										<span class="font-medium">Quittance de loyer</span>
										<span class="mt-0.5 block text-xs text-slate-500 dark:text-slate-400">Générateur gratuit</span>
									</a>
									<a
										href="/calendrier-fiscal"
										class="block rounded-lg px-3 py-2.5 text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700"
										onclick={() => (simulateursOpen = false)}
									>
										<span class="font-medium">Calendrier fiscal SCI</span>
										<span class="mt-0.5 block text-xs text-slate-500 dark:text-slate-400">Dates clés 2026</span>
									</a>
									<a
										href="/simulateur-plus-value"
										class="block rounded-lg px-3 py-2.5 text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700"
										onclick={() => (simulateursOpen = false)}
									>
										<span class="font-medium">Plus-value immobilière</span>
										<span class="mt-0.5 block text-xs text-slate-500 dark:text-slate-400">Impôt sur la cession</span>
									</a>
								</div>
							</div>
							{/if}
						</div>
					</div>
					<div class="hidden items-center gap-3 md:flex">
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
							onclick={() => (mobileMenuOpen = false)}
							class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Tarifs
						</a>
						<p class="px-4 pt-2 text-xs font-semibold tracking-wider text-slate-400 uppercase dark:text-slate-500">Simulateurs</p>
						<a
							href="/simulateur-cerfa"
							onclick={() => (mobileMenuOpen = false)}
							class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							CERFA 2044
						</a>
						<a
							href="/generateur-quittance"
							onclick={() => (mobileMenuOpen = false)}
							class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Quittance de loyer
						</a>
						<a
							href="/calendrier-fiscal"
							onclick={() => (mobileMenuOpen = false)}
							class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Calendrier fiscal SCI
						</a>
						<a
							href="/simulateur-plus-value"
							onclick={() => (mobileMenuOpen = false)}
							class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Plus-value immobilière
						</a>
						<div class="my-1 border-t border-slate-200 dark:border-slate-800"></div>
						<a
							href="/login"
							onclick={() => (mobileMenuOpen = false)}
							class="rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Connexion
						</a>
						<a
							href="/register"
							onclick={() => (mobileMenuOpen = false)}
							class="rounded-2xl bg-gradient-to-r from-blue-500 to-cyan-500 px-4 py-3 text-center text-sm font-medium text-white transition-colors hover:from-blue-600 hover:to-cyan-600"
						>
							Inscription
						</a>
					</div>
				</div>
			{/if}
		</nav>
	{/if}

	{#if page.url.pathname === '/'}
		{#if authResolved && user}
			<section class="flex min-h-[60vh] items-center justify-center">
				<p class="animate-pulse text-sm text-slate-500">Redirection vers le tableau de bord…</p>
			</section>
		{:else}
			<div id="main-content">{@render children()}</div>
		{/if}
	{:else if isPublicRoute(page.url.pathname)}
		<div id="main-content">{@render children()}</div>
	{:else if isProtectedRoute(page.url.pathname) && !authResolved}
		<!-- Silent wait while Supabase restores session from storage -->
		<section class="flex min-h-[60vh] items-center justify-center">
			<div class="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600"></div>
		</section>
	{:else if isProtectedRoute(page.url.pathname) && !user}
		<!-- Silent redirect handled by $effect — show spinner, not a "Zone protégée" card
		     that would flash on F5/hard-refresh while Supabase restores the session. -->
		<section class="flex min-h-[60vh] items-center justify-center">
			<div class="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600"></div>
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
						<h3 class="font-semibold text-slate-900 dark:text-slate-100">GérerSCI</h3>
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
									href="/simulateur-plus-value"
									class="text-slate-600 transition-colors hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
									>Simulateur Plus-Value</a
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
							© 2026 GérerSCI. Tous droits réservés.
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
	<CookieBanner />
	<OfflineBanner />
</div>

<style>
	/* View Transitions API — smooth page-to-page fade */
	@keyframes fade-in {
		from { opacity: 0; }
	}
	@keyframes fade-out {
		to { opacity: 0; }
	}
	:global(::view-transition-old(root)) {
		animation: 250ms ease-out fade-out;
	}
	:global(::view-transition-new(root)) {
		animation: 250ms ease-in fade-in;
	}

	/* Respect reduced motion preference */
	@media (prefers-reduced-motion: reduce) {
		:global(::view-transition-old(root)),
		:global(::view-transition-new(root)) {
			animation: none;
		}
	}
</style>
