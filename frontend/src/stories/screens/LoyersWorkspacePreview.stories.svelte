<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import LoyersWorkspacePreview from './LoyersWorkspacePreview.svelte';

	const { Story } = defineMeta({
		title: 'Screens/Loyers Workspace',
		component: LoyersWorkspacePreview,
		tags: ['autodocs'],
		parameters: {
			layout: 'fullscreen'
		}
	});
</script>

<Story name="Desktop" />
