function parseBooleanFeatureFlag(value: string | boolean | undefined, fallback = true): boolean {
	if (typeof value === 'boolean') {
		return value;
	}
	if (typeof value !== 'string') {
		return fallback;
	}

	const normalized = value.trim().toLowerCase();
	if (!normalized) {
		return fallback;
	}
	if (['1', 'true', 'yes', 'on', 'enabled'].includes(normalized)) {
		return true;
	}
	if (['0', 'false', 'no', 'off', 'disabled'].includes(normalized)) {
		return false;
	}
	return fallback;
}

export const featureFlags = {
	multiSciDashboardV2: parseBooleanFeatureFlag(
		import.meta.env.PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2,
		true
	)
};

export { parseBooleanFeatureFlag };
