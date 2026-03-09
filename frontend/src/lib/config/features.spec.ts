import { describe, expect, it } from 'vitest';

import { parseBooleanFeatureFlag } from './features';

describe('parseBooleanFeatureFlag', () => {
	it('returns the fallback when the value is missing', () => {
		expect(parseBooleanFeatureFlag(undefined, true)).toBe(true);
		expect(parseBooleanFeatureFlag(undefined, false)).toBe(false);
	});

	it('parses truthy string values', () => {
		expect(parseBooleanFeatureFlag('true')).toBe(true);
		expect(parseBooleanFeatureFlag('YES')).toBe(true);
		expect(parseBooleanFeatureFlag('1')).toBe(true);
	});

	it('parses falsy string values', () => {
		expect(parseBooleanFeatureFlag('false')).toBe(false);
		expect(parseBooleanFeatureFlag('off')).toBe(false);
		expect(parseBooleanFeatureFlag('0')).toBe(false);
	});

	it('keeps the fallback on unknown values', () => {
		expect(parseBooleanFeatureFlag('ship-it', true)).toBe(true);
		expect(parseBooleanFeatureFlag('ship-it', false)).toBe(false);
	});
});
