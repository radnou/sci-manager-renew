<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import BiensWorkspacePreview from './BiensWorkspacePreview.svelte';

	const { Story } = defineMeta({
		title: 'Screens/Biens Workspace',
		component: BiensWorkspacePreview,
		tags: ['autodocs'],
		parameters: {
			layout: 'fullscreen'
		}
	});
</script>

<Story name="Desktop" />
