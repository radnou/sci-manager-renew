import { writable } from 'svelte/store';

export type ToastVariant = 'default' | 'success' | 'error';

export type ToastItem = {
	id: number;
	title: string;
	description?: string;
	variant: ToastVariant;
	timeoutMs: number;
};

const toastsStore = writable<ToastItem[]>([]);
let nextToastId = 1;

export const toasts = {
	subscribe: toastsStore.subscribe
};

export function dismissToast(id: number) {
	toastsStore.update((current) => current.filter((toast) => toast.id !== id));
}

export function addToast(input: {
	title: string;
	description?: string;
	variant?: ToastVariant;
	timeoutMs?: number;
}) {
	const toast: ToastItem = {
		id: nextToastId++,
		title: input.title,
		description: input.description,
		variant: input.variant ?? 'default',
		timeoutMs: input.timeoutMs ?? 4200
	};

	toastsStore.update((current) => [toast, ...current].slice(0, 5));

	if (toast.timeoutMs > 0) {
		setTimeout(() => {
			dismissToast(toast.id);
		}, toast.timeoutMs);
	}

	return toast.id;
}
