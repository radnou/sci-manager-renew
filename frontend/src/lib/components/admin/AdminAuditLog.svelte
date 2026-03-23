<script lang="ts">
	type AuditEntry = {
		id: string;
		admin_action: string;
		target_user_id: string | null;
		details: Record<string, unknown>;
		ip_address: string | null;
		created_at: string;
	};

	let {
		entries,
		total,
		page,
		onPageChange
	}: {
		entries: AuditEntry[];
		total: number;
		page: number;
		onPageChange: (page: number) => void;
	} = $props();

	const perPage = 50;
	const totalPages = $derived(Math.ceil(total / perPage));

	const actionBadge: Record<string, string> = {
		plan_change: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
		send_email: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
		disable_user: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
		take_snapshot: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
	};

	function relativeTime(iso: string): string {
		const diff = Date.now() - new Date(iso).getTime();
		const mins = Math.floor(diff / 60000);
		if (mins < 1) return "à l'instant";
		if (mins < 60) return `il y a ${mins}min`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `il y a ${hrs}h`;
		const days = Math.floor(hrs / 24);
		return `il y a ${days}j`;
	}
</script>

<div class="rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
	<div class="overflow-x-auto">
		<table class="w-full text-sm">
			<thead class="border-b border-slate-200 dark:border-slate-700">
				<tr>
					<th class="px-4 py-3 text-left text-xs font-medium text-slate-500">Date</th>
					<th class="px-4 py-3 text-left text-xs font-medium text-slate-500">Action</th>
					<th class="px-4 py-3 text-left text-xs font-medium text-slate-500">Utilisateur cible</th>
					<th class="px-4 py-3 text-left text-xs font-medium text-slate-500">Détails</th>
					<th class="px-4 py-3 text-left text-xs font-medium text-slate-500">IP</th>
				</tr>
			</thead>
			<tbody class="divide-y divide-slate-100 dark:divide-slate-800">
				{#each entries as entry}
					<tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50">
						<td class="px-4 py-3 whitespace-nowrap text-slate-600 dark:text-slate-400">
							{relativeTime(entry.created_at)}
						</td>
						<td class="px-4 py-3">
							<span
								class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium {actionBadge[
									entry.admin_action
								] || 'bg-slate-100 text-slate-600'}"
							>
								{entry.admin_action}
							</span>
						</td>
						<td class="px-4 py-3 font-mono text-xs text-slate-500">
							{entry.target_user_id ? entry.target_user_id.slice(0, 8) + '...' : '—'}
						</td>
						<td class="max-w-xs truncate px-4 py-3 text-xs text-slate-500">
							{JSON.stringify(entry.details)}
						</td>
						<td class="px-4 py-3 font-mono text-xs text-slate-400">
							{entry.ip_address || '—'}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	{#if totalPages > 1}
		<div
			class="flex items-center justify-between border-t border-slate-200 px-4 py-3 dark:border-slate-700"
		>
			<span class="text-sm text-slate-500">{total} entrées</span>
			<div class="flex gap-1">
				<button
					onclick={() => onPageChange(page - 1)}
					disabled={page <= 1}
					class="rounded px-3 py-1 text-sm hover:bg-slate-100 disabled:opacity-40 dark:hover:bg-slate-800"
					>←</button
				>
				<span class="px-3 py-1 text-sm text-slate-600 dark:text-slate-400">{page}/{totalPages}</span
				>
				<button
					onclick={() => onPageChange(page + 1)}
					disabled={page >= totalPages}
					class="rounded px-3 py-1 text-sm hover:bg-slate-100 disabled:opacity-40 dark:hover:bg-slate-800"
					>→</button
				>
			</div>
		</div>
	{/if}
</div>
