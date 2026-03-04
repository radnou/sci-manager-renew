<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import BrandFoundations from './BrandFoundations.svelte';

	const { Story } = defineMeta({
		title: 'Foundations/Brand Foundations',
		component: BrandFoundations,
		tags: ['autodocs'],
		parameters: {
			layout: 'fullscreen'
		}
	});
</script>

<Story name="Visual Language" />
