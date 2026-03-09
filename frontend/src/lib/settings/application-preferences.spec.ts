import { beforeEach, describe, expect, it } from 'vitest';

import {
	APPLICATION_PREFERENCES_STORAGE_KEY,
	DEFAULT_APPLICATION_PREFERENCES,
	readApplicationPreferences,
	saveApplicationPreferences
} from './application-preferences';

describe('application preferences storage', () => {
	beforeEach(() => {
		const storage = new Map<string, string>();
		Object.defineProperty(globalThis, 'window', {
			configurable: true,
			value: {
				localStorage: {
					getItem: (key: string) => storage.get(key) ?? null,
					setItem: (key: string, value: string) => {
						storage.set(key, value);
					},
					removeItem: (key: string) => {
						storage.delete(key);
					},
					clear: () => {
						storage.clear();
					}
				}
			}
		});
		window.localStorage.clear();
	});

	it('returns defaults when nothing has been saved yet', () => {
		expect(readApplicationPreferences()).toEqual(DEFAULT_APPLICATION_PREFERENCES);
	});

	it('merges saved values over the defaults', () => {
		window.localStorage.setItem(
			APPLICATION_PREFERENCES_STORAGE_KEY,
			JSON.stringify({
				defaultLandingRoute: '/scis',
				density: 'compact',
				showPdfPreview: false
			})
		);

		expect(readApplicationPreferences()).toEqual({
			...DEFAULT_APPLICATION_PREFERENCES,
			defaultLandingRoute: '/scis',
			density: 'compact',
			showPdfPreview: false
		});
	});

	it('saves preferences in local storage', () => {
		const nextPreferences = {
			...DEFAULT_APPLICATION_PREFERENCES,
			defaultLandingRoute: '/settings' as const,
			riskAlertsEnabled: false
		};

		saveApplicationPreferences(nextPreferences);

		expect(window.localStorage.getItem(APPLICATION_PREFERENCES_STORAGE_KEY)).toBe(
			JSON.stringify(nextPreferences)
		);
	});

	it('accepts the connected hubs as landing routes', () => {
		window.localStorage.setItem(
			APPLICATION_PREFERENCES_STORAGE_KEY,
			JSON.stringify({
				defaultLandingRoute: '/finance'
			})
		);

		expect(readApplicationPreferences()).toEqual({
			...DEFAULT_APPLICATION_PREFERENCES,
			defaultLandingRoute: '/finance'
		});
	});
});
