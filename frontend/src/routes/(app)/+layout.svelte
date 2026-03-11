<script lang="ts">
	import { setContext } from 'svelte';
	import AppSidebarV2 from '$lib/components/AppSidebarV2.svelte';

	const props = $props<{ data: any; children: any }>();

	setContext('user', props.data.user);
	setContext('subscription', props.data.subscription);
</script>

<div class="flex min-h-screen">
	<AppSidebarV2 user={props.data.user} />
	<main class="flex-1 overflow-auto">
		{@render props.children()}
	</main>
</div>
