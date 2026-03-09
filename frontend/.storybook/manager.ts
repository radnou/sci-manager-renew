import { addons } from 'storybook/manager-api';
import { create } from 'storybook/theming/create';

const gerersciTheme = create({
	base: 'light',
	brandTitle: 'GererSCI • Design System',
	brandUrl: '/',
	brandTarget: '_self',
	colorPrimary: '#0f766e',
	colorSecondary: '#0369a1',
	appBg: '#f1f5f9',
	appContentBg: '#ffffff',
	appPreviewBg: '#f8fafc',
	appBorderColor: '#cbd5e1',
	appBorderRadius: 10,
	fontBase: '"Space Grotesk", "Avenir Next", "Trebuchet MS", sans-serif',
	fontCode: '"IBM Plex Mono", Menlo, Consolas, monospace',
	textColor: '#0f172a',
	textInverseColor: '#ffffff',
	barTextColor: '#334155',
	barSelectedColor: '#0f766e',
	barHoverColor: '#0f766e',
	barBg: '#ffffff',
	inputBg: '#ffffff',
	inputBorder: '#cbd5e1',
	inputTextColor: '#0f172a',
	inputBorderRadius: 8
});

addons.setConfig({
	theme: gerersciTheme,
	panelPosition: 'right',
	showNav: true,
	showPanel: true,
	enableShortcuts: true
});
