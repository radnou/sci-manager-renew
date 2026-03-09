<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import TabBar from '$lib/components/TabBar.svelte';

	const { Story } = defineMeta({
		title: 'Components/TabBar',
		component: TabBar
	});
</script>

<Story name="Default">
	<TabBar
		tabs={[
			{ id: 'flux', label: 'Flux' },
			{ id: 'patrimoine', label: 'Patrimoine' },
			{ id: 'documents', label: 'Documents' },
			{ id: 'gouvernance', label: 'Gouvernance' },
			{ id: 'analytique', label: 'Analytique' }
		]}
		activeTab="flux"
	/>
</Story>

<Story name="With Badge">
	<TabBar
		tabs={[
			{ id: 'flux', label: 'Flux', badge: 3 },
			{ id: 'patrimoine', label: 'Patrimoine' },
			{ id: 'documents', label: 'Documents' }
		]}
		activeTab="flux"
	/>
</Story>
