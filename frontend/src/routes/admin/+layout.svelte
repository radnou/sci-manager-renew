<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { page } from '$app/state';
	import { adminKey } from '$lib/stores/admin-auth';

	let { children } = $props();
	let authorized = $state(false);
	let loading = $state(false);
	let keyInput = $state('');
	let error = $state('');

	const adminNav = [
		{ href: '/admin', label: 'Dashboard', exact: true },
		{ href: '/admin/users', label: 'Utilisateurs', exact: false },
		{ href: '/admin/revenue', label: 'Revenue', exact: false },
		{ href: '/admin/audit', label: 'Audit Log', exact: false }
	];

	const currentPath = $derived(page.url.pathname);

	function isActive(item: (typeof adminNav)[0]): boolean {
		if (item.exact) return currentPath === item.href;
		return currentPath.startsWith(item.href);
	}

	onMount(async () => {
		// Check if we already have a key in sessionStorage
		const existingKey = get(adminKey);
		if (existingKey) {
			try {
				const resp = await fetch('/api/v1/admin/metrics', {
					headers: { 'X-Admin-Key': existingKey }
				});
				if (resp.ok) {
					authorized = true;
					return;
				}
			} catch {
				// Key expired or invalid, ask again
			}
			adminKey.set('');
		}
	});

	async function login() {
		if (!keyInput.trim()) return;
		loading = true;
		error = '';
		try {
			const resp = await fetch('/api/v1/admin/metrics', {
				headers: { 'X-Admin-Key': keyInput.trim() }
			});
			if (!resp.ok) throw new Error('Unauthorized');
			adminKey.set(keyInput.trim());
			authorized = true;
		} catch {
			error = 'Clé incorrecte ou non autorisée.';
		} finally {
			loading = false;
		}
	}

	function logout() {
		adminKey.set('');
		authorized = false;
		keyInput = '';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') login();
	}
</script>

{#if !authorized}
	<!-- Login screen — dark bg with red accent -->
	<div class="flex min-h-screen items-center justify-center bg-slate-950">
		<div class="w-full max-w-sm rounded-2xl border border-red-900/30 bg-slate-900 p-8 shadow-2xl">
			<div class="mb-6 flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-red-600">
					<span class="text-lg font-bold text-white">A</span>
				</div>
				<div>
					<h1 class="text-xl font-bold text-white">Admin Panel</h1>
					<p class="text-xs text-red-400">GérerSCI — Accès restreint</p>
				</div>
			</div>
			<input
				type="password"
				placeholder="Clé admin..."
				bind:value={keyInput}
				onkeydown={handleKeydown}
				class="mb-3 h-10 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 text-sm text-white placeholder:text-slate-500 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
			/>
			{#if error}
				<p class="mb-3 text-xs text-red-400">{error}</p>
			{/if}
			<button
				onclick={login}
				disabled={loading || !keyInput.trim()}
				class="w-full rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50"
			>
				{loading ? 'Vérification...' : 'Accéder'}
			</button>
		</div>
	</div>
{:else}
	<!-- Admin shell — dark theme with red accent bar -->
	<div class="min-h-screen bg-slate-950">
		<!-- Top bar -->
		<div class="border-b border-red-900/30 bg-slate-900">
			<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 md:px-8">
				<div class="flex items-center gap-3">
					<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-red-600">
						<span class="text-sm font-bold text-white">A</span>
					</div>
					<span class="text-sm font-semibold text-white">GérerSCI Admin</span>
					<span
						class="rounded-full bg-red-950/60 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-red-200 border border-red-800/30"
					>
						Production
					</span>
				</div>
				<button
					onclick={logout}
					class="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-400 hover:bg-slate-800 hover:text-white"
				>
					Déconnexion
				</button>
			</div>
		</div>

		<!-- Nav tabs -->
		<div class="border-b border-slate-800 bg-slate-900/50">
			<nav class="mx-auto flex max-w-7xl gap-1 px-4 md:px-8">
				{#each adminNav as item}
					<a
						href={item.href}
						class="relative px-4 py-3 text-sm font-medium transition-colors {isActive(item)
							? 'text-red-400'
							: 'text-slate-400 hover:text-slate-200'}"
					>
						{item.label}
						{#if isActive(item)}
							<div class="absolute bottom-0 left-0 right-0 h-0.5 bg-red-500"></div>
						{/if}
					</a>
				{/each}
			</nav>
		</div>

		<!-- Content -->
		<div class="mx-auto max-w-7xl px-4 py-6 md:px-8">
			{@render children()}
		</div>
	</div>
{/if}
