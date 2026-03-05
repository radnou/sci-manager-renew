<script lang="ts">
	import { onMount } from 'svelte';
	import type { User } from '@supabase/supabase-js';
	import { page } from '$app/state';
	import { locales, localizeHref } from '$lib/paraglide/runtime';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Toaster } from '$lib/components/ui/toast';
	import { theme } from '$lib/stores/theme';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import CookieConsent from '$lib/components/CookieConsent.svelte';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
	let user = $state<User | null>(null);

	onMount(() => {
		let mounted = true;

		// Initialize theme
		theme.initialize();

		supabase.auth.getSession().then(({ data }) => {
			if (mounted) {
				user = data.session?.user ?? null;
			}
		});

		const {
			data: { subscription }
		} = supabase.auth.onAuthStateChange((_event, session) => {
			if (mounted) {
				user = session?.user ?? null;
			}
		});

		return () => {
			mounted = false;
			subscription.unsubscribe();
		};
	});

	async function handleLogout() {
		await supabase.auth.signOut();
	}
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div class="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-50 transition-colors">
	<nav class="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/95">
		<div class="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 md:px-8">
			<a href="/" class="font-bold text-xl tracking-tight text-slate-900 dark:text-slate-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
				SCI Manager
			</a>
			<div class="flex items-center gap-6">
				<!-- Navigation links for authenticated users -->
				{#if user}
					<div class="hidden md:flex items-center gap-6">
						<a href="/dashboard" class="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
							Dashboard
						</a>
						<a href="/biens" class="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
							Biens
						</a>
						<a href="/loyers" class="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
							Loyers
						</a>
						<a href="/pricing" class="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
							Tarifs
						</a>
					</div>
					<div class="flex items-center gap-3">
						<span class="hidden sm:inline text-sm text-slate-600 dark:text-slate-400">
							{user.email}
						</span>
						<Button variant="outline" size="sm" onclick={handleLogout}>
							Déconnexion
						</Button>
					</div>
				{:else}
					<div class="hidden md:flex items-center gap-4">
						<a href="/pricing" class="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
							Tarifs
						</a>
					</div>
					<div class="flex items-center gap-3">
						<a href="/login">
							<Button variant="ghost" size="sm">Connexion</Button>
						</a>
						<a href="/register">
							<Button size="sm" class="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white border-0">
								Inscription
							</Button>
						</a>
					</div>
				{/if}
				<ThemeToggle />
			</div>
		</div>

		<!-- Mobile navigation for authenticated users -->
		{#if user}
			<div class="md:hidden border-t border-slate-200 dark:border-slate-800">
				<div class="flex items-center justify-around px-4 py-2">
					<a href="/dashboard" class="flex flex-col items-center gap-1 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
						<span>Dashboard</span>
					</a>
					<a href="/biens" class="flex flex-col items-center gap-1 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
						<span>Biens</span>
					</a>
					<a href="/loyers" class="flex flex-col items-center gap-1 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
						<span>Loyers</span>
					</a>
					<a href="/pricing" class="flex flex-col items-center gap-1 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
						<span>Tarifs</span>
					</a>
				</div>
			</div>
		{/if}
	</nav>

	{@render children()}

	<!-- Footer -->
	<footer class="border-t border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
		<div class="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
			<div class="grid gap-8 md:grid-cols-4">
				<div class="space-y-4">
					<h3 class="font-semibold text-slate-900 dark:text-slate-100">SCI Manager</h3>
					<p class="text-sm text-slate-600 dark:text-slate-400">
						Pilotez votre SCI comme un opérateur avec des outils professionnels.
					</p>
				</div>

				<div class="space-y-4">
					<h4 class="font-medium text-slate-900 dark:text-slate-100">Produit</h4>
					<ul class="space-y-2 text-sm">
						<li><a href="/pricing" class="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">Tarifs</a></li>
						<li><a href="/#features" class="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">Fonctionnalités</a></li>
						<li><a href="/conseils-big4" class="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">Conseils Big4</a></li>
					</ul>
				</div>

				<div class="space-y-4">
					<h4 class="font-medium text-slate-900 dark:text-slate-100">Support</h4>
					<ul class="space-y-2 text-sm">
						<li><a href="/help" class="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">Aide</a></li>
						<li><a href="/contact" class="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">Contact</a></li>
						<li><a href="/privacy" class="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">Confidentialité</a></li>
					</ul>
				</div>

				<div class="space-y-4">
					<h4 class="font-medium text-slate-900 dark:text-slate-100">Entreprise</h4>
					<ul class="space-y-2 text-sm">
						<li><a href="/about" class="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">À propos</a></li>
						<li><a href="/blog" class="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">Blog</a></li>
						<li><a href="/careers" class="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors">Carrières</a></li>
					</ul>
				</div>
			</div>

			<div class="mt-8 border-t border-slate-200 dark:border-slate-800 pt-8">
				<div class="flex flex-col items-center justify-between gap-4 sm:flex-row">
					<p class="text-sm text-slate-600 dark:text-slate-400">
						© 2024 SCI Manager. Tous droits réservés.
					</p>
					<div class="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
						<span>🇫🇷 Fait en France</span>
						<span>•</span>
						<span>RGPD Compliant</span>
					</div>
				</div>
			</div>
		</div>
	</footer>

	<Toaster />
	<CookieConsent />
</div>

<div style="display:none">
	{#each locales as locale (locale)}
		<a href={localizeHref(page.url.pathname, { locale })}>{locale}</a>
	{/each}
</div>
