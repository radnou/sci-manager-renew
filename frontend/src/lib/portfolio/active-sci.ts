import { browser } from '$app/environment';

export const ACTIVE_SCI_STORAGE_KEY = 'sci-manager.active-sci-id';

export function getStoredActiveSciId() {
	if (!browser) {
		return null;
	}

	const value = window.localStorage.getItem(ACTIVE_SCI_STORAGE_KEY);
	return value && value.trim().length > 0 ? value : null;
}

export function setStoredActiveSciId(id: string | null | undefined) {
	if (!browser) {
		return;
	}

	if (!id || id.trim().length === 0) {
		window.localStorage.removeItem(ACTIVE_SCI_STORAGE_KEY);
		return;
	}

	window.localStorage.setItem(ACTIVE_SCI_STORAGE_KEY, id);
}
