<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import BienForm from '$lib/components/BienForm.svelte';

	const { Story } = defineMeta({
		title: 'Components/Bien Form',
		component: BienForm,
		tags: ['autodocs'],
		args: {
			title: 'Nouveau bien',
			description: 'Crée un actif avec statut d’occupation et loyer estimé.',
			submitting: false
		}
	});
</script>

<Story name="Default" />
<Story name="Submitting" args={{ submitting: true }} />
