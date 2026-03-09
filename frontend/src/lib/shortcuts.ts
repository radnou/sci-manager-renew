/**
 * Global keyboard shortcuts registry.
 * Register shortcuts once from +layout.svelte; they auto-clean on unmount.
 */

export type ShortcutHandler = (event: KeyboardEvent) => void;

export interface ShortcutDefinition {
	/** Key to match (e.g. "k", "p", "/") */
	key: string;
	/** Require Cmd (Mac) or Ctrl (Win/Linux) */
	mod?: boolean;
	/** Require Shift */
	shift?: boolean;
	/** Handler to invoke */
	handler: ShortcutHandler;
	/** Human-readable label for command palette */
	label?: string;
}

const shortcuts: ShortcutDefinition[] = [];

export function registerShortcut(def: ShortcutDefinition): () => void {
	shortcuts.push(def);
	return () => {
		const idx = shortcuts.indexOf(def);
		if (idx !== -1) shortcuts.splice(idx, 1);
	};
}

export function handleGlobalKeydown(event: KeyboardEvent): void {
	// Skip when typing in inputs
	const target = event.target as HTMLElement | null;
	if (
		target &&
		(target.tagName === 'INPUT' ||
			target.tagName === 'TEXTAREA' ||
			target.tagName === 'SELECT' ||
			target.isContentEditable)
	) {
		return;
	}

	const isMod = event.metaKey || event.ctrlKey;

	for (const def of shortcuts) {
		const modMatch = def.mod ? isMod : !isMod;
		const shiftMatch = def.shift ? event.shiftKey : !event.shiftKey;
		if (event.key.toLowerCase() === def.key.toLowerCase() && modMatch && shiftMatch) {
			event.preventDefault();
			def.handler(event);
			return;
		}
	}
}

export function getRegisteredShortcuts(): ReadonlyArray<ShortcutDefinition> {
	return shortcuts;
}
