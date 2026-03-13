<script module lang="ts">
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import QuitusGenerator from '$lib/components/QuitusGenerator.svelte';

	const mockGenerateQuitus = async () =>
		new Blob(['%PDF-1.4\n% Mock quittus\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'], {
			type: 'application/pdf'
		});

	const failingGenerateQuitus = async () => {
		throw new Error('Simulation API: génération indisponible');
	};

	const { Story } = defineMeta({
		title: 'Components/Quitus Generator',
		component: QuitusGenerator,
		tags: ['autodocs'],
		args: {
			title: 'Quittance PDF',
			description: "Production d\u2019un quittus à la demande.",
			buttonLabel: 'Générer le quittus',
			generateQuitus: mockGenerateQuitus
		}
	});
</script>

<Story name="Default" />
<Story name="Error Scenario" args={{ generateQuitus: failingGenerateQuitus }} />
