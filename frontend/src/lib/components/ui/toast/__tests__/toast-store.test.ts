import { describe, it, expect, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { addToast, dismissToast, handleUndo, flushPendingDeletes, toasts } from '../toast-store';

describe('toast-store', () => {
	beforeEach(() => {
		// Drain all existing toasts between tests
		const current = get(toasts);
		current.forEach((t) => dismissToast(t.id));
	});

	// ── addToast ────────────────────────────────────────────

	it('addToast adds a toast to the store with default variant', () => {
		const id = addToast({ title: 'Hello' });
		const items = get(toasts);
		const toast = items.find((t) => t.id === id);
		expect(toast).toBeDefined();
		expect(toast?.title).toBe('Hello');
		expect(toast?.variant).toBe('default');
	});

	it('addToast with variant undo creates an undo toast with callbacks', () => {
		const onUndo = vi.fn();
		const onExpire = vi.fn();
		const id = addToast({
			title: 'Element supprime',
			variant: 'undo',
			undoCallbacks: { onUndo, onExpire },
			timeoutMs: 60000
		});
		const items = get(toasts);
		const toast = items.find((t) => t.id === id);
		expect(toast?.variant).toBe('undo');
		expect(toast?.undoCallbacks?.onUndo).toBe(onUndo);
		expect(toast?.undoCallbacks?.onExpire).toBe(onExpire);
	});

	// ── flushPendingDeletes ─────────────────────────────────

	it('flushPendingDeletes calls onExpire for all undo toasts and removes them', () => {
		const onExpire1 = vi.fn();
		const onExpire2 = vi.fn();
		addToast({
			title: 'Undo A',
			variant: 'undo',
			undoCallbacks: { onUndo: vi.fn(), onExpire: onExpire1 },
			timeoutMs: 60000
		});
		addToast({
			title: 'Undo B',
			variant: 'undo',
			undoCallbacks: { onUndo: vi.fn(), onExpire: onExpire2 },
			timeoutMs: 60000
		});
		// Non-undo toast should survive
		addToast({ title: 'Success toast', variant: 'success' });

		flushPendingDeletes();

		expect(onExpire1).toHaveBeenCalledOnce();
		expect(onExpire2).toHaveBeenCalledOnce();

		const remaining = get(toasts);
		expect(remaining.every((t) => t.variant !== 'undo')).toBe(true);
		expect(remaining.some((t) => t.title === 'Success toast')).toBe(true);
	});

	// ── handleUndo ──────────────────────────────────────────

	it('handleUndo calls onUndo callback and removes the toast', () => {
		const onUndo = vi.fn();
		const onExpire = vi.fn();
		const id = addToast({
			title: 'Supprime',
			variant: 'undo',
			undoCallbacks: { onUndo, onExpire },
			timeoutMs: 60000
		});

		handleUndo(id);

		expect(onUndo).toHaveBeenCalledOnce();
		expect(onExpire).not.toHaveBeenCalled();
		const items = get(toasts);
		expect(items.find((t) => t.id === id)).toBeUndefined();
	});

	// ── dismissToast ────────────────────────────────────────

	it('dismissToast removes toast by id', () => {
		const id = addToast({ title: 'Temporary', timeoutMs: 0 });
		expect(get(toasts).find((t) => t.id === id)).toBeDefined();
		dismissToast(id);
		expect(get(toasts).find((t) => t.id === id)).toBeUndefined();
	});
});
