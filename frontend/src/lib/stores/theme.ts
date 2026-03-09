import { writable } from 'svelte/store';
import { browser } from '$app/environment';

type Theme = 'light' | 'dark';

function normalizeTheme(value: string | null): Theme | null {
	if (value === 'light' || value === 'dark') return value;
	return null;
}

function applyTheme(nextTheme: Theme, withTransition: boolean) {
	if (!browser) return;

	localStorage.setItem('theme', nextTheme);
	document.documentElement.classList.toggle('dark', nextTheme === 'dark');

	if (!withTransition) return;
	document.documentElement.style.setProperty('--theme-transition', 'all 0.3s ease');
	setTimeout(() => {
		document.documentElement.style.removeProperty('--theme-transition');
	}, 300);
}

function createThemeStore() {
	const { subscribe, set, update } = writable<Theme>('light');

	return {
		subscribe,
		toggle: () =>
			update((theme) => {
				const newTheme = theme === 'light' ? 'dark' : 'light';
				applyTheme(newTheme, true);
				return newTheme;
			}),
		set: (theme: Theme) => {
			const nextTheme = theme === 'light' ? 'light' : 'dark';
			set(nextTheme);
			applyTheme(nextTheme, true);
		},
		initialize: () => {
			if (!browser) return;

			const savedTheme = normalizeTheme(localStorage.getItem('theme'));
			const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
			const initialTheme: Theme = savedTheme ?? (prefersDark ? 'dark' : 'light');

			set(initialTheme);
			applyTheme(initialTheme, false);
		}
	};
}

export const theme = createThemeStore();
