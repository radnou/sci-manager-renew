<script lang="ts">
	import { setContext } from 'svelte';
	import { page } from '$app/state';
	import AppNavbar from '$lib/components/AppNavbar.svelte';
	import DemoBanner from '$lib/components/DemoBanner.svelte';
	import DemoConversionPrompt from '$lib/components/DemoConversionPrompt.svelte';

	const props = $props<{ data: any; children: any }>();

	// svelte-ignore state_referenced_locally
	setContext('user', props.data?.user);
	// svelte-ignore state_referenced_locally
	setContext('subscription', props.data?.subscription);

	let showConversionPrompt = $state(false);

	$effect(() => {
		// Access page.url to trigger on navigation
		const _ = page.url.pathname;

		if (props.data?.subscription && !props.data.subscription?.is_active) {
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

{#if !props.data?.user}
	<!-- Auth resolving -- root layout handles redirect when confirmed no session -->
	<section class="flex min-h-[60vh] items-center justify-center">
		<div class="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600"></div>
	</section>
{:else}
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
{/if}
