<script lang="ts">
	import { onMount } from 'svelte';
	import { apiFetch } from '$lib/api';

	type AdminUser = {
		id: string;
		email: string;
		created_at: string;
		plan_key: string;
		is_active: boolean;
		stripe_customer_id: string | null;
	};

	let users = $state<AdminUser[]>([]);
	let page = $state(1);

	async function loadUsers() {
		try {
			const data: { users: AdminUser[] } = await apiFetch(
				`/api/v1/admin/users?page=${page}&per_page=50`
			);
			users = data.users;
		} catch {
			// handled by layout guard
		}
	}

	onMount(loadUsers);
</script>

<svelte:head>
	<title>Utilisateurs | Admin | GererSCI</title>
</svelte:head>

<div
	class="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950"
>
	<div class="overflow-x-auto">
		<table class="w-full text-left text-sm">
			<thead>
				<tr class="border-b border-slate-200 dark:border-slate-800">
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Email</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Plan</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Actif</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Inscription</th>
				</tr>
			</thead>
			<tbody>
				{#each users as user (user.id)}
					<tr
						class="border-b border-slate-100 transition-colors hover:bg-slate-50 dark:border-slate-800/50 dark:hover:bg-slate-900"
					>
						<td class="px-4 py-3 font-medium text-slate-900 dark:text-slate-100"
							>{user.email}</td
						>
						<td class="px-4 py-3">
							<span
								class="rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize
								{user.plan_key === 'pro'
									? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
									: user.plan_key === 'lifetime'
										? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
										: user.plan_key === 'starter'
											? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
											: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}"
							>
								{user.plan_key}
							</span>
						</td>
						<td class="px-4 py-3">
							{#if user.is_active}
								<span class="text-green-600">Oui</span>
							{:else}
								<span class="text-slate-400">Non</span>
							{/if}
						</td>
						<td class="px-4 py-3 text-slate-500"
							>{new Date(user.created_at).toLocaleDateString('fr-FR')}</td
						>
					</tr>
				{:else}
					<tr>
						<td colspan="4" class="px-4 py-8 text-center text-slate-500"
							>Aucun utilisateur trouvé</td
						>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>

<div class="mt-4 flex gap-2">
	<button
		class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-300"
		disabled={page === 1}
		onclick={() => {
			page--;
			loadUsers();
		}}
	>
		Précédent
	</button>
	<span class="px-3 py-1.5 text-sm text-slate-500">Page {page}</span>
	<button
		class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300"
		onclick={() => {
			page++;
			loadUsers();
		}}
	>
		Suivant
	</button>
</div>
