<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { getCurrentSession } from '$lib/auth/session';
	import { apiClient } from '$lib/api';

	let { children } = $props();
	let authorized = $state(false);
	let loading = $state(true);

	const adminNav = [
		{ href: '/admin', label: 'Dashboard' },
		{ href: '/admin/users', label: 'Utilisateurs' }
	];

	onMount(async () => {
		const session = await getCurrentSession();
		if (!session?.user) {
			goto('/login');
			return;
		}

		try {
			const res = await apiClient('/api/v1/admin/stats');
			if (res.ok) {
				authorized = true;
			} else {
				goto('/dashboard');
			}
		} catch {
			goto('/dashboard');
		} finally {
			loading = false;
		}
	});
</script>

{#if loading}
	<div class="flex items-center justify-center py-20">
		<p class="text-sm text-slate-500">Vérification des droits...</p>
	</div>
{:else if authorized}
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
					class="rounded-lg px-4 py-2 text-sm font-medium transition-colors {page.url.pathname ===
					item.href
						? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
						: 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300'}"
				>
					{item.label}
				</a>
			{/each}
		</nav>

		{@render children()}
	</div>
{/if}
