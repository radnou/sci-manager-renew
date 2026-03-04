import { describe, expect, it } from 'vitest';
import { formatEur, formatFrDate } from './formatters';

describe('high-value formatters', () => {
	it('formats euro values in fr-FR style', () => {
		expect(formatEur(1450)).toContain('1');
		expect(formatEur(1450)).toContain('€');
	});

	it('returns fallback for invalid amounts', () => {
		expect(formatEur(undefined, 'Non renseigné')).toBe('Non renseigné');
		expect(formatEur(Number.NaN, 'Non renseigné')).toBe('Non renseigné');
	});

	it('formats valid dates and preserves unknown strings', () => {
		expect(formatFrDate('2026-03-01')).toMatch(/2026/);
		expect(formatFrDate('invalid-date')).toBe('invalid-date');
		expect(formatFrDate('', 'Aucune date')).toBe('Aucune date');
	});
});
