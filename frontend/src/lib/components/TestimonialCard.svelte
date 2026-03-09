<script lang="ts">
	import { Card, CardContent } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Star, Quote } from 'lucide-svelte';

	interface Props {
		quote: string;
		author: string;
		role: string;
		company?: string;
		rating?: number;
		avatar?: string;
		class?: string;
	}

	let { quote, author, role, company, rating = 5, avatar, class: className = '' }: Props = $props();
</script>

<Card
	class="relative overflow-hidden border-slate-200/60 bg-white/80 shadow-lg backdrop-blur-sm transition-all duration-300 hover:shadow-xl dark:border-slate-700/60 dark:bg-slate-800/80 {className}"
>
	<CardContent class="p-6">
		<div class="flex items-start gap-4">
			{#if avatar}
				<img
					src={avatar}
					alt={author}
					class="h-12 w-12 rounded-full object-cover ring-2 ring-slate-200 dark:ring-slate-700"
				/>
			{:else}
				<div
					class="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 text-lg font-semibold text-white"
				>
					{author.charAt(0).toUpperCase()}
				</div>
			{/if}

			<div class="flex-1">
				<Quote class="mb-3 h-6 w-6 text-slate-400 dark:text-slate-500" />

				<blockquote class="mb-4 text-slate-700 dark:text-slate-300">
					"{quote}"
				</blockquote>

				<div class="flex items-center justify-between">
					<div>
						<div class="font-semibold text-slate-900 dark:text-slate-100">
							{author}
						</div>
						<div class="text-sm text-slate-600 dark:text-slate-400">
							{role}
							{#if company}
								<span class="text-slate-400 dark:text-slate-500"> • {company}</span>
							{/if}
						</div>
					</div>

					<div class="flex items-center gap-1">
						{#each Array(rating) as _}
							<Star class="h-4 w-4 fill-amber-400 text-amber-400" />
						{/each}
					</div>
				</div>
			</div>
		</div>
	</CardContent>
</Card>
