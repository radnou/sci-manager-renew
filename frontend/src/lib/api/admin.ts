import { apiFetch } from './client';

export function fetchAdminMetrics() {
	return apiFetch<{
		north_star: { value: number; previous: number; trend: string; change_pct: number | null };
		mrr: { value: number; previous: number; trend: string; change_pct: number | null };
		activation_rate: { value: number; previous: number; trend: string; change_pct: number | null };
		churn_30d: { value: number; previous: number; trend: string; change_pct: number | null };
		conversion_rate: { value: number; previous: number; trend: string; change_pct: number | null };
	}>('/api/v1/admin/metrics');
}

export function fetchAdminAlerts() {
	return apiFetch<{
		alerts: Array<{
			type: string;
			severity: 'high' | 'medium' | 'info';
			message: string;
			detail: string;
			tooltip: string;
		}>;
	}>('/api/v1/admin/alerts');
}

export function fetchAdminFunnel() {
	return apiFetch<{
		steps: Array<{ label: string; count: number; rate: number }>;
		bottleneck_index: number;
	}>('/api/v1/admin/funnel');
}

export function fetchAdminUsers(
	params: {
		search?: string;
		status?: string;
		plan?: string;
		sort?: string;
		page?: number;
		per_page?: number;
	} = {}
) {
	const searchParams = new URLSearchParams();
	if (params.search) searchParams.set('search', params.search);
	if (params.status) searchParams.set('status', params.status);
	if (params.plan) searchParams.set('plan', params.plan);
	if (params.sort) searchParams.set('sort', params.sort);
	if (params.page) searchParams.set('page', String(params.page));
	if (params.per_page) searchParams.set('per_page', String(params.per_page));
	const qs = searchParams.toString();
	return apiFetch<{
		users: Array<{
			id: string;
			email: string;
			created_at: string;
			plan_key: string;
			is_active: boolean;
			sci_count: number;
			biens_count: number;
			loyers_30d: number;
			last_activity: string | null;
			status: string;
			stripe_customer_id: string | null;
		}>;
		total: number;
		page: number;
		per_page: number;
	}>(`/api/v1/admin/users${qs ? `?${qs}` : ''}`);
}
