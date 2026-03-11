import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { addToast, dismissToast, handleUndo, flushPendingDeletes, toasts } from '../toast-store';

describe('toast-store undo', () => {
	beforeEach(() => {
		// Clear all toasts
		const current = get(toasts);
		current.forEach(t => dismissToast(t.id));
	});

	it('adds a basic toast', () => {
		const id = addToast({ title: 'Hello' });
		const items = get(toasts);
		expect(items.some(t => t.id === id)).toBe(true);
		expect(items.find(t => t.id === id)?.variant).toBe('default');
	});

	it('adds an undo toast with callbacks', () => {
		const onUndo = vi.fn();
		const onExpire = vi.fn();
		const id = addToast({
			title: 'Supprimé',
			variant: 'undo',
			undoCallbacks: { onUndo, onExpire },
			timeoutMs: 50000
		});
		const items = get(toasts);
		const toast = items.find(t => t.id === id);
		expect(toast?.variant).toBe('undo');
		expect(toast?.undoCallbacks).toBeTruthy();
	});

	it('handleUndo calls onUndo and removes toast', () => {
		const onUndo = vi.fn();
		const onExpire = vi.fn();
		const id = addToast({
			title: 'Test',
			variant: 'undo',
			undoCallbacks: { onUndo, onExpire },
			timeoutMs: 50000
		});
		handleUndo(id);
		expect(onUndo).toHaveBeenCalledOnce();
		expect(onExpire).not.toHaveBeenCalled();
		const items = get(toasts);
		expect(items.find(t => t.id === id)).toBeUndefined();
	});

	it('flushPendingDeletes calls onExpire for all undo toasts', () => {
		const onExpire1 = vi.fn();
		const onExpire2 = vi.fn();
		addToast({
			title: 'A',
			variant: 'undo',
			undoCallbacks: { onUndo: vi.fn(), onExpire: onExpire1 },
			timeoutMs: 50000
		});
		addToast({
			title: 'B',
			variant: 'undo',
			undoCallbacks: { onUndo: vi.fn(), onExpire: onExpire2 },
			timeoutMs: 50000
		});
		addToast({ title: 'Normal', variant: 'success' });

		flushPendingDeletes();
		expect(onExpire1).toHaveBeenCalledOnce();
		expect(onExpire2).toHaveBeenCalledOnce();

		const remaining = get(toasts);
		expect(remaining.every(t => t.variant !== 'undo')).toBe(true);
	});

	it('dismissToast removes toast by id', () => {
		const id = addToast({ title: 'Bye', timeoutMs: 0 });
		dismissToast(id);
		const items = get(toasts);
		expect(items.find(t => t.id === id)).toBeUndefined();
	});
});
