<script lang="ts">
	import type { Associe } from '$lib/api';
	import { Users } from 'lucide-svelte';
	import { formatPercent } from '$lib/high-value/formatters';
	import { mapAssociateRoleLabel } from '$lib/high-value/presentation';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';

	interface Props {
		associates: Associe[];
	}

	let { associates }: Props = $props();
</script>

<Card class="sci-section-card">
	<CardHeader>
		<CardTitle class="flex items-center gap-2 text-lg">
			<Users class="h-5 w-5 text-cyan-600" />
			Associés et gouvernance
		</CardTitle>
		<CardDescription>
			Répartition du capital et rôle opérationnel sur la SCI active.
		</CardDescription>
	</CardHeader>
	<CardContent class="space-y-3">
		{#if associates.length === 0}
			<p
				class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
			>
				Aucun associé disponible sur la SCI active.
			</p>
		{:else}
			{#each associates as associe (String(associe.id))}
				<div
					class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
				>
					<div class="flex items-start justify-between gap-3">
						<div>
							<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">{associe.nom}</p>
							<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
								{associe.email || 'Email non renseigné'}
							</p>
						</div>
						<span
							class="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-semibold text-white dark:bg-slate-100 dark:text-slate-950"
						>
							{associe.part ? formatPercent(associe.part) : 'Part N/A'}
						</span>
					</div>
					<p class="mt-3 text-xs font-semibold tracking-[0.18em] text-slate-500 uppercase">
						{mapAssociateRoleLabel(associe.role)}
					</p>
				</div>
			{/each}
		{/if}
	</CardContent>
</Card>
