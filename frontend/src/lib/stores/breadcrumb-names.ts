import { writable } from 'svelte/store';

// Maps route segment values (UUIDs/IDs) to display names
// e.g., { "550e8400-...": "SCI Mosa Belleville", "abc-123": "15 rue de la Paix" }
export const breadcrumbNames = writable<Record<string, string>>({});
