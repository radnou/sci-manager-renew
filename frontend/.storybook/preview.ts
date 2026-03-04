import type { Preview } from '@storybook/sveltekit';
import '../src/routes/layout.css';

const preview: Preview = {
	parameters: {
		layout: 'padded',
		controls: {
			sort: 'requiredFirst',
			matchers: {
				color: /(background|color)$/i,
				date: /Date$/i
			}
		},
		backgrounds: {
			default: 'linen',
			values: [
				{ name: 'linen', value: '#f8fafc' },
				{ name: 'slate', value: '#0f172a' },
				{ name: 'paper', value: '#ffffff' }
			]
		},
		options: {
			storySort: {
				order: ['Introduction', 'Foundations', 'Components', 'Screens']
			}
		},
		a11y: {
			test: 'todo'
		}
	}
};

export default preview;
