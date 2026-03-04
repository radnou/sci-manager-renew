<script lang="ts">
	import { onMount } from 'svelte';
	import type { User } from '@supabase/supabase-js';
	import { page } from '$app/state';
	import { locales, localizeHref } from '$lib/paraglide/runtime';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Toaster } from '$lib/components/ui/toast';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
	let user = $state<User | null>(null);

	onMount(() => {
		let mounted = true;

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

<div class="dark min-h-screen bg-slate-950 text-slate-50">
	<nav class="border-b border-slate-800 bg-slate-950/95 backdrop-blur-md">
		<div class="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3 md:px-8">
			<a href="/" class="font-semibold tracking-tight text-slate-100">SCI Manager</a>
			{#if user}
				<div class="flex items-center gap-2">
					<a href="/dashboard" class="rounded-md px-2 py-1 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
						>Dashboard</a
					>
					<a href="/biens" class="rounded-md px-2 py-1 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
						>Biens</a
					>
					<a href="/loyers" class="rounded-md px-2 py-1 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
						>Loyers</a
					>
					<Button variant="outline" size="sm" onclick={handleLogout}>Logout</Button>
				</div>
			{:else}
				<div class="flex items-center gap-2">
					<Button variant="ghost" size="sm" href="/login">Connexion</Button>
					<Button size="sm" href="/register">Inscription</Button>
				</div>
			{/if}
		</div>
	</nav>

	{@render children()}
	<Toaster />
</div>

<div style="display:none">
	{#each locales as locale (locale)}
		<a href={localizeHref(page.url.pathname, { locale })}>{locale}</a>
	{/each}
</div>
