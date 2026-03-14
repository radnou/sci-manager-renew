<script lang="ts">
	import { setContext } from 'svelte';
	import AppNavbar from '$lib/components/AppNavbar.svelte';

	const props = $props<{ data: any; children: any }>();

	// svelte-ignore state_referenced_locally
	setContext('user', props.data.user);
	// svelte-ignore state_referenced_locally
	setContext('subscription', props.data.subscription);
</script>

<AppNavbar user={props.data.user} subscription={props.data.subscription} />

<main class="pb-12">
	{@render props.children()}
</main>
