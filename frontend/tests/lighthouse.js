import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

async function runLighthouse() {
	const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
	/** @type {import('lighthouse').Flags} */
	const options = { logLevel: 'info', output: 'html', port: chrome.port };
	const runnerResult = await lighthouse('http://localhost:5173', options);
	if (!runnerResult) {
		await chrome.kill();
		throw new Error('Lighthouse n’a retourné aucun résultat.');
	}

	const scores = runnerResult.lhr.categories;
	const performanceScore = scores.performance.score ?? 0;
	const accessibilityScore = scores.accessibility.score ?? 0;
	const bestPracticesScore = scores['best-practices'].score ?? 0;
	const seoScore = scores.seo.score ?? 0;
	console.log('Performance:', performanceScore * 100);
	console.log('Accessibility:', accessibilityScore * 100);
	console.log('Best Practices:', bestPracticesScore * 100);
	console.log('SEO:', seoScore * 100);

	await chrome.kill();

	// Assert scores > 95
	if (performanceScore < 0.95) process.exit(1);
	if (accessibilityScore < 0.95) process.exit(1);
}

runLighthouse();
