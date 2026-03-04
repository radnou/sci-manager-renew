<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import BienTable from '$lib/components/BienTable.svelte';

	const sampleBiens = [
		{ adresse: '14 rue Saint-Honoré', ville: 'Paris', loyer_cc: 1450, statut: 'occupe' },
		{ adresse: '8 avenue des Tilleuls', ville: 'Lyon', loyer_cc: 980, statut: 'vacant' },
		{ adresse: '21 quai Richelieu', ville: 'Bordeaux', loyer_cc: 1275, statut: 'travaux' }
	];

	const { Story } = defineMeta({
		title: 'Components/Bien Table',
		component: BienTable,
		tags: ['autodocs'],
		args: {
			title: 'Portefeuille immobilier',
			description: 'Vue consolidée des actifs en gestion.',
			biens: sampleBiens,
			loading: false
		}
	});
</script>

<Story name="Default" />
<Story name="Empty" args={{ biens: [] }} />
<Story name="Loading" args={{ loading: true }} />
