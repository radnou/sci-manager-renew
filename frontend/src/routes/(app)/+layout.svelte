<script lang="ts">
	import { setContext } from 'svelte';
	import { page } from '$app/stores';
	import AppNavbar from '$lib/components/AppNavbar.svelte';
	import DemoBanner from '$lib/components/DemoBanner.svelte';
	import DemoConversionPrompt from '$lib/components/DemoConversionPrompt.svelte';

	const props = $props<{ data: any; children: any }>();

	// svelte-ignore state_referenced_locally
	setContext('user', props.data.user);
	// svelte-ignore state_referenced_locally
	setContext('subscription', props.data.subscription);

	let showConversionPrompt = $state(false);

	$effect(() => {
		// Access page.url to trigger on navigation
		const _ = $page.url.pathname;

		if (!props.data.subscription?.is_active) {
			const count = parseInt(localStorage.getItem('demo_page_visits') || '0') + 1;
			localStorage.setItem('demo_page_visits', String(count));

			if (count === 3) {
				const dismissed = localStorage.getItem('demo_prompt_dismissed');
				if (!dismissed || Date.now() - parseInt(dismissed) > 600000) {
					showConversionPrompt = true;
				}
			}
		}
	});
</script>

<AppNavbar user={props.data.user} subscription={props.data.subscription} />

{#if !props.data.subscription?.is_active}
	<DemoBanner />
{/if}

<main class="pb-12">
	{@render props.children()}
</main>

{#if showConversionPrompt}
	<DemoConversionPrompt
		message="Vous explorez depuis quelques minutes. Prêt à gérer vos vraies SCI ?"
		open={showConversionPrompt}
		onClose={() => { showConversionPrompt = false; }}
	/>
{/if}
