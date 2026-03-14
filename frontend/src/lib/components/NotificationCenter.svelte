<script lang="ts">
	import { onMount } from 'svelte';
	import { Bell, Check, CheckCheck } from 'lucide-svelte';
	import { notifications } from '$lib/stores/notifications';
	import { Button } from '$lib/components/ui/button';

	let open = $state(false);

	onMount(() => {
		notifications.load();
	});

	function formatTimeAgo(dateStr: string): string {
		const diff = Date.now() - new Date(dateStr).getTime();
		const minutes = Math.floor(diff / 60000);
		if (minutes < 1) return 'À l\'instant';
		if (minutes < 60) return `Il y a ${minutes}min`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `Il y a ${hours}h`;
		const days = Math.floor(hours / 24);
		return `Il y a ${days}j`;
	}

	function typeIcon(type: string) {
		switch (type) {
			case 'late_payment': return 'text-rose-500';
			case 'status_change': return 'text-cyan-500';
			case 'document_ready': return 'text-emerald-500';
			default: return 'text-slate-500';
		}
	}
</script>

<div class="relative">
	<button
		type="button"
		class="relative rounded-full p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
		onclick={() => (open = !open)}
		aria-label="Notifications"
		aria-haspopup="dialog"
		aria-expanded={open}
	>
		<Bell class="h-4.5 w-4.5" />
		{#if $notifications.unreadCount > 0}
			<span class="absolute -right-0.5 -top-0.5 flex h-4.5 w-4.5 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white">
				{$notifications.unreadCount > 9 ? '9+' : $notifications.unreadCount}
			</span>
		{/if}
	</button>

	{#if open}
		<div
			class="absolute right-0 top-full z-50 mt-2 w-80 rounded-2xl border border-slate-200 bg-white shadow-lg dark:border-slate-800 dark:bg-slate-950"
			role="dialog"
			aria-label="Centre de notifications"
		>
			<div class="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
				<h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Notifications</h3>
				{#if $notifications.unreadCount > 0}
					<button
						type="button"
						class="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
						onclick={() => notifications.markAllRead()}
					>
						<CheckCheck class="h-3.5 w-3.5" />
						Tout lire
					</button>
				{/if}
			</div>

			<div class="max-h-80 overflow-y-auto" role="list" aria-label="Liste des notifications">
				{#if $notifications.items.length === 0}
					<div class="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
						Aucune notification
					</div>
				{:else}
					{#each $notifications.items as notification (notification.id)}
						<button
							type="button"
							class="flex w-full gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-900 {notification.read_at ? 'opacity-60' : ''}"
							onclick={() => {
								if (!notification.read_at) notifications.markRead(notification.id);
							}}
						>
							<div class="mt-0.5 h-2 w-2 flex-shrink-0 rounded-full {notification.read_at ? 'bg-transparent' : 'bg-blue-500'}"></div>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-medium text-slate-900 dark:text-slate-100">{notification.title}</p>
								<p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">{notification.message}</p>
								<p class="mt-1 text-[10px] {typeIcon(notification.type)}">{formatTimeAgo(notification.created_at)}</p>
							</div>
						</button>
					{/each}
				{/if}
			</div>
		</div>
	{/if}
</div>
