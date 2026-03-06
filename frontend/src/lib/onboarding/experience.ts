import { browser } from '$app/environment';

const DISMISSED_PREFIX = 'sci-manager.onboarding.dismissed';

function buildDismissedKey(userId: string) {
	return `${DISMISSED_PREFIX}:${userId}`;
}

export function isOnboardingDismissed(userId: string) {
	if (!browser || !userId) {
		return false;
	}

	return window.localStorage.getItem(buildDismissedKey(userId)) === 'true';
}

export function dismissOnboarding(userId: string) {
	if (!browser || !userId) {
		return;
	}

	window.localStorage.setItem(buildDismissedKey(userId), 'true');
}

export function reopenOnboarding(userId: string) {
	if (!browser || !userId) {
		return;
	}

	window.localStorage.removeItem(buildDismissedKey(userId));
}
