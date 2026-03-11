import { writable, derived } from 'svelte/store';
import type { SCIDetail } from '$lib/api';

export const currentSci = writable<SCIDetail | null>(null);
export const currentSciId = derived(currentSci, ($sci) => $sci?.id ?? null);
export const userRole = writable<'gerant' | 'associe'>('associe');
export const isGerant = derived(userRole, ($role) => $role === 'gerant');
