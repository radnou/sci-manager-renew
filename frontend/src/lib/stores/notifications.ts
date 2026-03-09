import { writable } from 'svelte/store';
import { fetchNotifications, fetchUnreadCount, markNotificationRead, markAllNotificationsRead, type Notification } from '$lib/api';

function createNotificationStore() {
	const { subscribe, set, update } = writable<{
		items: Notification[];
		unreadCount: number;
		loading: boolean;
	}>({
		items: [],
		unreadCount: 0,
		loading: false
	});

	return {
		subscribe,

		async load() {
			update((s) => ({ ...s, loading: true }));
			try {
				const [items, { count }] = await Promise.all([
					fetchNotifications(),
					fetchUnreadCount()
				]);
				set({ items, unreadCount: count, loading: false });
			} catch {
				update((s) => ({ ...s, loading: false }));
			}
		},

		async markRead(id: string) {
			await markNotificationRead(id);
			update((s) => ({
				...s,
				items: s.items.map((n) =>
					n.id === id ? { ...n, read_at: new Date().toISOString() } : n
				),
				unreadCount: Math.max(0, s.unreadCount - 1)
			}));
		},

		async markAllRead() {
			await markAllNotificationsRead();
			update((s) => ({
				...s,
				items: s.items.map((n) => ({ ...n, read_at: n.read_at || new Date().toISOString() })),
				unreadCount: 0
			}));
		}
	};
}

export const notifications = createNotificationStore();
