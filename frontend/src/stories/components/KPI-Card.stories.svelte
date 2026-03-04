<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import KpiCard from '$lib/components/KPI-Card.svelte';

	const { Story } = defineMeta({
		title: 'Components/KPI Card',
		component: KpiCard,
		tags: ['autodocs'],
		argTypes: {
			trend: {
				control: { type: 'select' },
				options: ['up', 'down', 'neutral']
			},
			tone: {
				control: { type: 'select' },
				options: ['default', 'success', 'warning', 'danger', 'accent']
			}
		},
		args: {
			label: 'Revenus locatifs',
			value: '18 420 €',
			caption: 'M-1 comparé',
			trend: 'up',
			trendValue: '+7.2%',
			tone: 'success',
			loading: false
		}
	});
</script>

<Story name="Default" />
<Story
	name="Warning"
	args={{ label: 'Retards', value: 4, caption: 'dossiers à traiter', trend: 'down', trendValue: 'urgence', tone: 'warning' }}
/>
<Story name="Loading" args={{ loading: true }} />
