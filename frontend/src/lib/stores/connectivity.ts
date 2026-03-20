import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type ConnectivityState = 'online' | 'offline' | 'reconnecting';

function createConnectivityStore() {
	const { subscribe, set } = writable<ConnectivityState>('online');

	if (browser) {
		set(navigator.onLine ? 'online' : 'offline');

		window.addEventListener('online', () => {
			set('reconnecting');
			// Brief "reconnecting" state before confirming online
			setTimeout(() => set('online'), 1500);
		});

		window.addEventListener('offline', () => {
			set('offline');
		});
	}

	return { subscribe };
}

export const connectivity = createConnectivityStore();
