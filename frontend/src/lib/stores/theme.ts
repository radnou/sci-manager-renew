import { writable } from 'svelte/store';
import { browser } from '$app/environment';

type Theme = 'light' | 'dark';

function createThemeStore() {
	const { subscribe, set, update } = writable<Theme>('dark');

	return {
		subscribe,
		toggle: () => update(theme => {
			const newTheme = theme === 'light' ? 'dark' : 'light';
			if (browser) {
				localStorage.setItem('theme', newTheme);
				document.documentElement.classList.toggle('dark', newTheme === 'dark');
				// Add smooth transition class
				document.documentElement.style.setProperty('--theme-transition', 'all 0.3s ease');
				setTimeout(() => {
					document.documentElement.style.removeProperty('--theme-transition');
				}, 300);
			}
			return newTheme;
		}),
		set: (theme: Theme) => {
			set(theme);
			if (browser) {
				localStorage.setItem('theme', theme);
				document.documentElement.classList.toggle('dark', theme === 'dark');
				// Add smooth transition class
				document.documentElement.style.setProperty('--theme-transition', 'all 0.3s ease');
				setTimeout(() => {
					document.documentElement.style.removeProperty('--theme-transition');
				}, 300);
			}
		},
		initialize: () => {
			if (browser) {
				const savedTheme = localStorage.getItem('theme') as Theme;
				const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
				const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');

				set(initialTheme);
				document.documentElement.classList.toggle('dark', initialTheme === 'dark');
			}
		}
	};
}

export const theme = createThemeStore();