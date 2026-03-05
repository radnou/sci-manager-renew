import { describe, expect, it } from 'vitest';
import { formatCompactNumber, formatEur, formatFrDate, formatPercent } from './formatters';

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

	it('formats percentages and compact numbers with fr-FR conventions', () => {
		expect(formatPercent(12.34)).toContain('%');
		expect(formatPercent(undefined, 'N/A')).toBe('N/A');
		expect(formatCompactNumber(2500)).not.toBe('2500');
		expect(formatCompactNumber(Number.NaN, '0')).toBe('0');
	});
});
