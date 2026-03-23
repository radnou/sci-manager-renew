import { apiFetch } from './client';
import type { Notification, NotificationPreference } from './types';

export function fetchNotifications(unreadOnly = false): Promise<Notification[]> {
	const params = unreadOnly ? '?unread_only=true' : '';
	return apiFetch<Notification[]>(`/api/v1/notifications/${params}`);
}

export function fetchUnreadCount(): Promise<{ count: number }> {
	return apiFetch<{ count: number }>('/api/v1/notifications/count');
}

export function markNotificationRead(id: string): Promise<Notification> {
	return apiFetch<Notification>(`/api/v1/notifications/${id}/read`, { method: 'PATCH' });
}

export function markAllNotificationsRead(): Promise<{ updated: number }> {
	return apiFetch<{ updated: number }>('/api/v1/notifications/read-all', { method: 'PATCH' });
}

export async function fetchNotificationPreferences(): Promise<{
	preferences: NotificationPreference[];
}> {
	return apiFetch<{ preferences: NotificationPreference[] }>(
		'/api/v1/user/notification-preferences'
	);
}

export async function updateNotificationPreferences(
	preferences: NotificationPreference[]
): Promise<{ preferences: NotificationPreference[] }> {
	return apiFetch<{ preferences: NotificationPreference[] }>(
		'/api/v1/user/notification-preferences',
		{
			method: 'PUT',
			body: JSON.stringify({ preferences })
		}
	);
}
