import { getCurrentSession } from '$lib/auth/session';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export class ApiError extends Error {
	constructor(
		public status: number,
		public code: string,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

export class AuthError extends ApiError {
	constructor(m: string) {
		super(401, 'auth_error', m);
		this.name = 'AuthError';
	}
}

export class ForbiddenError extends ApiError {
	constructor(m: string) {
		super(403, 'forbidden', m);
		this.name = 'ForbiddenError';
	}
}

export class PaymentRequiredError extends ApiError {
	constructor(
		m: string,
		public redirect?: string
	) {
		super(402, 'payment_required', m);
		this.name = 'PaymentRequiredError';
	}
}

export class ValidationError extends ApiError {
	constructor(m: string) {
		super(422, 'validation_error', m);
		this.name = 'ValidationError';
	}
}

export class NotFoundError extends ApiError {
	constructor(m: string) {
		super(404, 'not_found', m);
		this.name = 'NotFoundError';
	}
}

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
	let accessToken: string | undefined;
	try {
		const session = await getCurrentSession();
		accessToken = session?.access_token;
	} catch {
		accessToken = undefined;
	}

	const headers = new Headers(options?.headers);
	const isFormData = options?.body instanceof FormData;
	if (isFormData) {
		// Let the browser set Content-Type with boundary for FormData
		headers.delete('Content-Type');
	} else if (!headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}
	if (accessToken) {
		headers.set('Authorization', `Bearer ${accessToken}`);
	}

	const response = await fetch(`${API_URL}${endpoint}`, {
		...options,
		headers
	});

	if (!response.ok) {
		const message = await response.text();
		switch (response.status) {
			case 401:
				throw new AuthError(message || 'Unauthorized');
			case 402:
				throw new PaymentRequiredError(message || 'Payment Required');
			case 403:
				throw new ForbiddenError(message || 'Forbidden');
			case 404:
				throw new NotFoundError(message || 'Not Found');
			case 422:
				throw new ValidationError(message || 'Validation Error');
			default:
				throw new ApiError(
					response.status,
					'api_error',
					message || `API error: ${response.status} ${response.statusText}`
				);
		}
	}

	if (response.status === 204) {
		return undefined as T;
	}

	return (await response.json()) as T;
}

export async function apiFetchBlob(endpoint: string, options?: RequestInit): Promise<Blob> {
	let accessToken: string | undefined;
	try {
		const session = await getCurrentSession();
		accessToken = session?.access_token;
	} catch {
		accessToken = undefined;
	}

	const headers = new Headers(options?.headers);
	if (options?.body && !headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}
	if (accessToken) {
		headers.set('Authorization', `Bearer ${accessToken}`);
	}

	const response = await fetch(`${API_URL}${endpoint}`, {
		...options,
		headers
	});

	if (!response.ok) {
		const message = await response.text();
		switch (response.status) {
			case 401:
				throw new AuthError(message || 'Unauthorized');
			case 402:
				throw new PaymentRequiredError(message || 'Payment Required');
			case 403:
				throw new ForbiddenError(message || 'Forbidden');
			case 404:
				throw new NotFoundError(message || 'Not Found');
			case 422:
				throw new ValidationError(message || 'Validation Error');
			default:
				throw new ApiError(
					response.status,
					'api_error',
					message || `API error: ${response.status} ${response.statusText}`
				);
		}
	}

	return response.blob();
}
