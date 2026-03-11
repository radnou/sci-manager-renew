<script lang="ts">
	import { setContext } from 'svelte';

	const props = $props<{ data: any; children: any }>();

	setContext('user', props.data.user);
	setContext('subscription', props.data.subscription);
</script>

{@render props.children()}
