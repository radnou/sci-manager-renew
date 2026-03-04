<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import LoyerTable from '$lib/components/LoyerTable.svelte';

	const sampleLoyers = [
		{ id_bien: 'BIEN-001', date_loyer: '2026-03-01', montant: 1450, statut: 'paye' },
		{ id_bien: 'BIEN-003', date_loyer: '2026-03-01', montant: 980, statut: 'en_attente' },
		{ id_bien: 'BIEN-002', date_loyer: '2026-02-28', montant: 1275, statut: 'retard' }
	];

	const { Story } = defineMeta({
		title: 'Components/Loyer Table',
		component: LoyerTable,
		tags: ['autodocs'],
		args: {
			title: 'Journal des loyers',
			description: 'Contrôle mensuel des encaissements.',
			loyers: sampleLoyers,
			loading: false
		}
	});
</script>

<Story name="Default" />
<Story name="Empty" args={{ loyers: [] }} />
<Story name="Loading" args={{ loading: true }} />
