import { defineConfig } from 'vitest/config';

export default defineConfig({
	test: {
		environment: 'node',
		include: ['src/lib/api.spec.ts', 'src/lib/high-value/**/*.spec.ts'],
		coverage: {
			enabled: true,
			provider: 'v8',
			reporter: ['text', 'json-summary'],
			include: ['src/lib/api.ts', 'src/lib/high-value/**/*.ts'],
			thresholds: {
				lines: 85,
				functions: 85,
				statements: 85,
				branches: 70
			}
		}
	}
});
