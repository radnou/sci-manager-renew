<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { adminKey } from '$lib/stores/admin-auth';
	import AdminAuditLog from '$lib/components/admin/AdminAuditLog.svelte';

	let entries = $state<any[]>([]);
	let total = $state(0);
	let page = $state(1);
	let loading = $state(true);

	async function adminFetch<T>(path: string): Promise<T> {
		const resp = await fetch(path, { headers: { 'X-Admin-Key': get(adminKey) } });
		if (!resp.ok) throw new Error(`${resp.status}`);
		return resp.json();
	}

	async function loadAuditLog() {
		loading = true;
		try {
			const data = await adminFetch<{ entries: any[]; total: number }>(
				`/api/v1/admin/audit-log?page=${page}&per_page=50`
			);
			entries = data.entries;
			total = data.total;
		} catch {
			entries = [];
		} finally {
			loading = false;
		}
	}

	function handlePageChange(newPage: number) {
		page = newPage;
		loadAuditLog();
	}

	onMount(loadAuditLog);
</script>

<svelte:head>
	<title>Audit Log | Admin | GérerSCI</title>
</svelte:head>

{#if loading}
	<div class="flex items-center justify-center py-20">
		<div
			class="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-600"
		></div>
	</div>
{:else}
	<AdminAuditLog {entries} {total} {page} onPageChange={handlePageChange} />
{/if}
