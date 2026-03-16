<script lang="ts">
	import { onMount } from 'svelte';
	import { page as pageState } from '$app/state';
	import AdminUserStatusBadge from '$lib/components/admin/AdminUserStatusBadge.svelte';

	type EnrichedUser = {
		id: string;
		email: string;
		created_at: string;
		plan_key: string;
		is_active: boolean;
		sci_count: number;
		biens_count: number;
		loyers_30d: number;
		last_activity: string | null;
		status: string;
		stripe_customer_id: string | null;
	};

	let users = $state<EnrichedUser[]>([]);
	let total = $state(0);
	let page = $state(1);
	let search = $state('');
	let statusFilter = $state('');
	let planFilter = $state('');
	let sortBy = $state('created_at');
	let loading = $state(true);

	const perPage = 50;
	const totalPages = $derived(Math.ceil(total / perPage));
	const adminKey = $derived(pageState.url.searchParams.get('secret') ?? '');

	async function adminFetch<T>(path: string): Promise<T> {
		const resp = await fetch(
			`${path}${path.includes('?') ? '&' : '?'}key=${encodeURIComponent(adminKey)}`
		);
		if (!resp.ok) throw new Error(`${resp.status}`);
		return resp.json();
	}

	async function loadUsers() {
		loading = true;
		try {
			const params = new URLSearchParams();
			if (search) params.set('search', search);
			if (statusFilter) params.set('status', statusFilter);
			if (planFilter) params.set('plan', planFilter);
			params.set('sort', sortBy);
			params.set('page', String(page));
			params.set('per_page', String(perPage));
			const qs = params.toString();

			const data = await adminFetch<{
				users: EnrichedUser[];
				total: number;
				page: number;
				per_page: number;
			}>(`/api/v1/admin/users?${qs}`);
			users = data.users;
			total = data.total;
		} catch {
			// handled by layout guard
		} finally {
			loading = false;
		}
	}

	onMount(loadUsers);

	function applyFilters() {
		page = 1;
		loadUsers();
	}

	function relativeTime(dateStr: string | null): string {
		if (!dateStr) return 'Jamais';
		const diff = Date.now() - new Date(dateStr).getTime();
		const minutes = Math.floor(diff / 60000);
		if (minutes < 1) return "a l'instant";
		if (minutes < 60) return `il y a ${minutes} min`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `il y a ${hours}h`;
		const days = Math.floor(hours / 24);
		if (days === 1) return 'hier';
		if (days < 30) return `il y a ${days}j`;
		const months = Math.floor(days / 30);
		return `il y a ${months} mois`;
	}

	const planBadgeClass: Record<string, string> = {
		pro: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
		lifetime: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
		starter: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
		cabinet: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
		free: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
	};
</script>

<svelte:head>
	<title>Utilisateurs | Admin | GererSCI</title>
</svelte:head>

<!-- Filters -->
<div class="mb-4 flex flex-wrap items-center gap-3">
	<input
		type="text"
		placeholder="Rechercher par email..."
		bind:value={search}
		oninput={() => applyFilters()}
		class="h-9 w-64 rounded-lg border border-slate-200 bg-white px-3 text-sm placeholder:text-slate-400 focus:border-sky-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
	/>
	<select
		bind:value={statusFilter}
		onchange={() => applyFilters()}
		class="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
	>
		<option value="">Tous les statuts</option>
		<option value="power_user">Power user</option>
		<option value="prospect">Prospect chaud</option>
		<option value="at_risk">A risque</option>
		<option value="new">Nouveau</option>
		<option value="active">Actif</option>
	</select>
	<select
		bind:value={planFilter}
		onchange={() => applyFilters()}
		class="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
	>
		<option value="">Tous les plans</option>
		<option value="free">Free</option>
		<option value="starter">Starter</option>
		<option value="pro">Pro</option>
		<option value="lifetime">Lifetime</option>
	</select>
	<select
		bind:value={sortBy}
		onchange={() => applyFilters()}
		class="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
	>
		<option value="created_at">Tri: inscription</option>
		<option value="last_activity">Tri: activite</option>
	</select>
</div>

<!-- Table -->
<div class="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
	<div class="overflow-x-auto">
		<table class="w-full text-left text-sm">
			<thead>
				<tr class="border-b border-slate-200 dark:border-slate-800">
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Email</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Plan</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">SCIs</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Biens</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Activite</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Statut</th>
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
								class="rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize {planBadgeClass[
									user.plan_key
								] ?? planBadgeClass.free}"
							>
								{user.plan_key}
							</span>
						</td>
						<td class="px-4 py-3 text-slate-600 dark:text-slate-400">{user.sci_count}</td>
						<td class="px-4 py-3 text-slate-600 dark:text-slate-400">{user.biens_count}</td>
						<td class="px-4 py-3 text-slate-500">{relativeTime(user.last_activity)}</td>
						<td class="px-4 py-3">
							<AdminUserStatusBadge status={user.status} />
						</td>
					</tr>
				{:else}
					<tr>
						<td colspan="6" class="px-4 py-8 text-center text-slate-500"
							>Aucun utilisateur trouve</td
						>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>

<!-- Pagination -->
<div class="mt-4 flex items-center gap-2">
	<button
		class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-300"
		disabled={page === 1}
		onclick={() => {
			page--;
			loadUsers();
		}}
	>
		Precedent
	</button>
	<span class="px-3 py-1.5 text-sm text-slate-500">
		Page {page} / {totalPages || 1} ({total} users)
	</span>
	<button
		class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-300"
		disabled={page >= totalPages}
		onclick={() => {
			page++;
			loadUsers();
		}}
	>
		Suivant
	</button>
</div>
