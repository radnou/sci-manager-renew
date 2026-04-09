export const APPLICATION_PREFERENCES_STORAGE_KEY = 'gerersci.application-preferences';

export type ApplicationLandingRoute =
	| '/dashboard'
	| '/scis'
	| '/finances'
	| '/exploitation'
	| '/settings';
export type ApplicationDensity = 'comfortable' | 'compact';

export type ApplicationPreferences = {
	defaultLandingRoute: ApplicationLandingRoute;
	density: ApplicationDensity;
	showPdfPreview: boolean;
	emailDigestEnabled: boolean;
	riskAlertsEnabled: boolean;
	/** Default day-of-month (1-28) for rent generation when no SCI or bien override is set. */
	defaultJourLoyer: number;
};

export const DEFAULT_APPLICATION_PREFERENCES: ApplicationPreferences = {
	defaultLandingRoute: '/dashboard',
	density: 'comfortable',
	showPdfPreview: true,
	emailDigestEnabled: true,
	riskAlertsEnabled: true,
	defaultJourLoyer: 1
};

function canUseStorage() {
	return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

export function readApplicationPreferences(): ApplicationPreferences {
	if (!canUseStorage()) {
		return DEFAULT_APPLICATION_PREFERENCES;
	}

	const raw = window.localStorage.getItem(APPLICATION_PREFERENCES_STORAGE_KEY);
	if (!raw) {
		return DEFAULT_APPLICATION_PREFERENCES;
	}

	try {
		const parsed = JSON.parse(raw) as Partial<ApplicationPreferences>;
		return {
			...DEFAULT_APPLICATION_PREFERENCES,
			...parsed
		};
	} catch {
		return DEFAULT_APPLICATION_PREFERENCES;
	}
}

export function saveApplicationPreferences(preferences: ApplicationPreferences) {
	if (!canUseStorage()) {
		return;
	}

	window.localStorage.setItem(APPLICATION_PREFERENCES_STORAGE_KEY, JSON.stringify(preferences));
}
