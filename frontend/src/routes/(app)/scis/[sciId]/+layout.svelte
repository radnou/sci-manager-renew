<script lang="ts">
	import { setContext } from 'svelte';
	import { breadcrumbNames } from '$lib/stores/breadcrumb-names';

	const props = $props<{ data: any; children: any }>();

	setContext('sci', props.data.sci);
	setContext('userRole', props.data.userRole);
	setContext('sciId', props.data.sciId);

	$effect(() => {
		if (props.data.sciId && props.data.sci?.nom) {
			breadcrumbNames.update((n) => ({ ...n, [props.data.sciId]: props.data.sci.nom }));
		}
	});
</script>

{@render props.children()}
