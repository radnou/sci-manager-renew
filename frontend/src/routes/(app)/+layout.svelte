<script lang="ts">
	import { setContext } from 'svelte';
	import AppNavbar from '$lib/components/AppNavbar.svelte';

	const props = $props<{ data: any; children: any }>();

	setContext('user', props.data.user);
	setContext('subscription', props.data.subscription);
</script>

<AppNavbar user={props.data.user} subscription={props.data.subscription} />

<main class="pb-12">
	{@render props.children()}
</main>
