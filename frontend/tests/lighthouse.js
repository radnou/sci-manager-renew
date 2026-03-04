import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

async function runLighthouse() {
  const chrome = await chromeLauncher.launch({chromeFlags: ['--headless']});
  const options = {logLevel: 'info', output: 'html', port: chrome.port};
  const runnerResult = await lighthouse('http://localhost:5173', options);

  const scores = runnerResult.lhr.categories;
  console.log('Performance:', scores.performance.score * 100);
  console.log('Accessibility:', scores.accessibility.score * 100);
  console.log('Best Practices:', scores['best-practices'].score * 100);
  console.log('SEO:', scores.seo.score * 100);

  await chrome.kill();

  // Assert scores > 95
  if (scores.performance.score < 0.95) process.exit(1);
  if (scores.accessibility.score < 0.95) process.exit(1);
}

runLighthouse();