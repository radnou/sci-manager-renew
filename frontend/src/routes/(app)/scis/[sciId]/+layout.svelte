<script lang="ts">
	import { setContext } from 'svelte';

	const props = $props<{ data: any; children: any }>();

	setContext('sci', props.data.sci);
	setContext('userRole', props.data.userRole);
	setContext('sciId', props.data.sciId);
</script>

{@render props.children()}
