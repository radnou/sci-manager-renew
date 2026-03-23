import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const stored = browser ? sessionStorage.getItem('adminKey') ?? '' : '';
export const adminKey = writable<string>(stored);

// Persist to sessionStorage on change (survives navigation, cleared on tab close)
if (browser) {
	adminKey.subscribe((value) => {
		if (value) {
			sessionStorage.setItem('adminKey', value);
		} else {
			sessionStorage.removeItem('adminKey');
		}
	});
}
