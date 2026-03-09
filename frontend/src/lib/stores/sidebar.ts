import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const SIDEBAR_STORAGE_KEY = 'gerersci.sidebar-collapsed';

function createSidebarStore() {
	const stored = browser ? localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true' : false;
	const { subscribe, set, update } = writable(stored);

	return {
		subscribe,
		toggle: () =>
			update((collapsed) => {
				const next = !collapsed;
				if (browser) localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next));
				return next;
			}),
		collapse: () => {
			set(true);
			if (browser) localStorage.setItem(SIDEBAR_STORAGE_KEY, 'true');
		},
		expand: () => {
			set(false);
			if (browser) localStorage.setItem(SIDEBAR_STORAGE_KEY, 'false');
		}
	};
}

export const sidebarCollapsed = createSidebarStore();
