import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type ThemePreference = 'system' | 'light' | 'dark';
type ResolvedTheme = 'light' | 'dark';

function normalizeTheme(value: string | null): ThemePreference | null {
	if (value === 'system' || value === 'light' || value === 'dark') return value;
	return null;
}

function getSystemTheme(): ResolvedTheme {
	return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function resolveTheme(preference: ThemePreference): ResolvedTheme {
	return preference === 'system' ? getSystemTheme() : preference;
}

function applyTheme(nextTheme: ThemePreference, withTransition: boolean) {
	if (!browser) return;

	localStorage.setItem('theme', nextTheme);
	document.documentElement.dataset.theme = nextTheme;
	document.documentElement.classList.toggle('dark', resolveTheme(nextTheme) === 'dark');

	if (!withTransition) return;
	document.documentElement.style.setProperty('--theme-transition', 'all 0.3s ease');
	setTimeout(() => {
		document.documentElement.style.removeProperty('--theme-transition');
	}, 300);
}

function createThemeStore() {
	const { subscribe, set, update } = writable<ThemePreference>('light');
	let mediaQuery: MediaQueryList | null = null;
	let mediaListener: ((event: MediaQueryListEvent) => void) | null = null;

	function setupSystemListener() {
		if (!browser || mediaQuery) return;
		mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
		mediaListener = () => {
			const savedTheme = normalizeTheme(localStorage.getItem('theme'));
			if ((savedTheme ?? 'light') === 'system') {
				applyTheme('system', false);
			}
		};
		mediaQuery.addEventListener('change', mediaListener);
	}

	return {
		subscribe,
		toggle: () => update((theme) => {
			const cycle: ThemePreference[] = ['light', 'dark'];
			const nextTheme = cycle[(cycle.indexOf(theme) + 1) % cycle.length];
			applyTheme(nextTheme, true);
			return nextTheme;
		}),
		set: (theme: ThemePreference) => {
			const nextTheme: ThemePreference =
				theme === 'light' || theme === 'dark' || theme === 'system' ? theme : 'light';
			set(nextTheme);
			applyTheme(nextTheme, true);
		},
		resolve: (theme: ThemePreference) => resolveTheme(theme),
		initialize: () => {
			if (!browser) return;

			const savedTheme = normalizeTheme(localStorage.getItem('theme'));
			const initialTheme: ThemePreference = savedTheme ?? 'light';

			set(initialTheme);
			applyTheme(initialTheme, false);
			setupSystemListener();
		}
	};
}

export const theme = createThemeStore();
