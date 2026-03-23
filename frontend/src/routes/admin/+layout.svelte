<script lang="ts">
	import { onMount } from 'svelte';
	import { adminKey } from '$lib/stores/admin-auth';

	let { children } = $props();
	let authorized = $state(false);
	let loading = $state(false);
	let keyInput = $state('');
	let error = $state('');

	const adminNav = [
		{ href: '/admin', label: 'Dashboard' },
		{ href: '/admin/users', label: 'Utilisateurs' }
	];

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

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') login();
	}
</script>

{#if !authorized}
	<div class="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
		<div class="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
			<div class="mb-6 flex items-center gap-3">
				<h1 class="text-xl font-bold text-slate-900 dark:text-slate-100">Admin</h1>
				<span class="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700 dark:bg-red-900/30 dark:text-red-400">
					Restricted
				</span>
			</div>
			<p class="mb-4 text-sm text-slate-500">Entrez votre clé admin pour continuer.</p>
			<input
				type="password"
				placeholder="Clé admin..."
				bind:value={keyInput}
				onkeydown={handleKeydown}
				class="mb-3 h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm placeholder:text-slate-400 focus:border-sky-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
			/>
			{#if error}
				<p class="mb-3 text-xs text-red-600 dark:text-red-400">{error}</p>
			{/if}
			<button
				onclick={login}
				disabled={loading || !keyInput.trim()}
				class="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
			>
				{loading ? 'Vérification...' : 'Accéder'}
			</button>
		</div>
	</div>
{:else}
	<div class="mx-auto max-w-7xl px-4 py-6 md:px-8">
		<div class="mb-6 flex items-center gap-3">
			<h1 class="text-2xl font-bold text-slate-900 dark:text-slate-100">Admin</h1>
			<span
				class="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700 dark:bg-red-900/30 dark:text-red-400"
			>
				Restricted
			</span>
		</div>

		<nav class="mb-8 flex gap-2">
			{#each adminNav as item}
				<a
					href={item.href}
					class="rounded-lg px-4 py-2 text-sm font-medium transition-colors"
				>
					{item.label}
				</a>
			{/each}
		</nav>

		{@render children()}
	</div>
{/if}
