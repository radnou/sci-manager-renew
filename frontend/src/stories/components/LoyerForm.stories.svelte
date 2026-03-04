<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import LoyerForm from '$lib/components/LoyerForm.svelte';

	const { Story } = defineMeta({
		title: 'Components/Loyer Form',
		component: LoyerForm,
		tags: ['autodocs'],
		args: {
			title: 'Nouveau loyer',
			description: 'Saisie d’un encaissement mensuel avec statut de paiement.',
			submitting: false
		}
	});
</script>

<Story name="Default" />
<Story name="Submitting" args={{ submitting: true }} />
