import { apiFetch } from './client';
import type {
	CheckoutSessionRequestPayload,
	CheckoutSessionResponsePayload,
	SubscriptionEntitlements,
	OnboardingStatus,
	OnboardingProfile,
	OnboardingProfilePayload,
	DataExportResponse,
	DataSummaryResponse,
	AccountDeleteResponse
} from './types';

export function createCheckoutSession(payload: CheckoutSessionRequestPayload) {
	return apiFetch<CheckoutSessionResponsePayload>('/api/v1/stripe/create-checkout-session', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function fetchSubscriptionEntitlements() {
	return apiFetch<SubscriptionEntitlements>('/api/v1/stripe/subscription');
}

export function cancelSubscription() {
	return apiFetch<{ status: string; message: string }>('/api/v1/stripe/cancel-subscription', {
		method: 'POST'
	});
}

export function fetchOnboardingStatus() {
	return apiFetch<OnboardingStatus>('/api/v1/onboarding');
}

export function saveOnboardingProfile(payload: OnboardingProfilePayload) {
	return apiFetch<OnboardingProfile>('/api/v1/onboarding/profile', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function completeOnboarding() {
	return apiFetch<{ completed: boolean }>('/api/v1/onboarding/complete', { method: 'POST' });
}

export function exportUserData() {
	return apiFetch<DataExportResponse>('/api/v1/gdpr/data-export');
}

export function fetchDataSummary() {
	return apiFetch<DataSummaryResponse>('/api/v1/gdpr/data-summary');
}

export function deleteAccount() {
	return apiFetch<AccountDeleteResponse>('/api/v1/gdpr/account', {
		method: 'DELETE'
	});
}
