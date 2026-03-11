import { writable } from 'svelte/store';

export type ToastVariant = 'default' | 'success' | 'error' | 'undo';

export type UndoCallbacks = {
	onUndo: () => void;
	onExpire: () => void;
};

export type ToastItem = {
	id: number;
	title: string;
	description?: string;
	variant: ToastVariant;
	timeoutMs: number;
	undoCallbacks?: UndoCallbacks;
};

const toastsStore = writable<ToastItem[]>([]);
let nextToastId = 1;
const activeTimers = new Map<number, ReturnType<typeof setTimeout>>();

export const toasts = {
	subscribe: toastsStore.subscribe
};

export function dismissToast(id: number) {
	activeTimers.delete(id);
	toastsStore.update((current) => current.filter((toast) => toast.id !== id));
}

export function handleUndo(id: number) {
	let found: ToastItem | undefined;
	toastsStore.update((current) => {
		found = current.find((t) => t.id === id);
		return current.filter((t) => t.id !== id);
	});
	const timer = activeTimers.get(id);
	if (timer) clearTimeout(timer);
	activeTimers.delete(id);
	found?.undoCallbacks?.onUndo();
}

export function flushPendingDeletes() {
	let undoToasts: ToastItem[] = [];
	toastsStore.update((current) => {
		undoToasts = current.filter((t) => t.variant === 'undo' && t.undoCallbacks);
		return current.filter((t) => t.variant !== 'undo');
	});
	for (const toast of undoToasts) {
		const timer = activeTimers.get(toast.id);
		if (timer) clearTimeout(timer);
		activeTimers.delete(toast.id);
		toast.undoCallbacks?.onExpire();
	}
}

export function addToast(input: {
	title: string;
	description?: string;
	variant?: ToastVariant;
	timeoutMs?: number;
	undoCallbacks?: UndoCallbacks;
}) {
	const toast: ToastItem = {
		id: nextToastId++,
		title: input.title,
		description: input.description,
		variant: input.variant ?? 'default',
		timeoutMs: input.timeoutMs ?? 4200,
		undoCallbacks: input.undoCallbacks
	};

	toastsStore.update((current) => [toast, ...current].slice(0, 5));

	if (toast.timeoutMs > 0) {
		const timer = setTimeout(() => {
			if (toast.variant === 'undo' && toast.undoCallbacks) {
				toast.undoCallbacks.onExpire();
			}
			dismissToast(toast.id);
		}, toast.timeoutMs);
		activeTimers.set(toast.id, timer);
	}

	return toast.id;
}

if (typeof window !== 'undefined') {
	window.addEventListener('beforeunload', () => {
		flushPendingDeletes();
	});
}
