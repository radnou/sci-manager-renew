<script lang="ts">
	import type { Bien } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { formatEur } from '$lib/high-value/formatters';
	import { mapBienTypeClass, mapBienTypeLabel } from '$lib/high-value/biens';
	import * as Table from '$lib/components/ui/table';

	type BienAction = (bien: Bien) => void;

	let {
		biens = [],
		loading = false,
		title = 'Portefeuille immobilier',
		description = 'Vision opérationnelle des biens, villes et loyers mensuels.',
		onEdit = undefined,
		onDelete = undefined,
		busyRowId = '',
		actionDisabled = false
	}: {
		biens?: Bien[];
		loading?: boolean;
		title?: string;
		description?: string;
		onEdit?: BienAction | undefined;
		onDelete?: BienAction | undefined;
		busyRowId?: string;
		actionDisabled?: boolean;
	} = $props();
	let showActions = $derived(Boolean(onEdit || onDelete));
</script>

<Card class="sci-section-card">
	<CardHeader class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
		<div>
			<CardTitle class="text-lg">{title}</CardTitle>
			<CardDescription>{description}</CardDescription>
		</div>
		<p class="text-xs font-semibold tracking-[0.15em] text-slate-500 uppercase">
			{biens.length} enregistrements
		</p>
	</CardHeader>
	<CardContent class="pt-0">
		{#if loading}
			<div class="space-y-2" aria-live="polite">
				{#each Array.from({ length: 6 }) as _, index (index)}
					<div class="h-11 animate-pulse rounded-md bg-slate-100" data-index={index}></div>
				{/each}
			</div>
		{:else if biens.length === 0}
			<div class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
				<p class="text-sm font-medium text-slate-700">Aucun bien enregistré pour le moment.</p>
				<p class="mt-1 text-sm text-slate-500">
					Ajoute une première adresse pour démarrer le suivi SCI.
				</p>
			</div>
		{:else}
			<div class="overflow-x-auto">
				<Table.Root>
					<Table.Header>
						<Table.Row>
							<Table.Head class="px-3">Adresse</Table.Head>
							<Table.Head class="px-3">Ville</Table.Head>
							<Table.Head class="px-3">Type</Table.Head>
							<Table.Head class="px-3 text-right">Loyer CC</Table.Head>
							<Table.Head class="px-3 text-right">Charges</Table.Head>
							{#if showActions}
								<Table.Head class="px-3 text-right">Actions</Table.Head>
							{/if}
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#each biens as bien (String(bien.id ?? `${bien.adresse}-${bien.code_postal ?? ''}`))}
							<Table.Row>
								<Table.Cell class="px-3 py-3 font-medium text-slate-900">{bien.adresse}</Table.Cell>
								<Table.Cell class="px-3 py-3 text-slate-700">{bien.ville || '—'}</Table.Cell>
								<Table.Cell class="px-3 py-3">
									<span
										class={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${mapBienTypeClass(bien.type_locatif)}`}
									>
										{mapBienTypeLabel(bien.type_locatif)}
									</span>
								</Table.Cell>
								<Table.Cell class="px-3 py-3 text-right font-medium text-slate-900">
									{formatEur(bien.loyer_cc, 'Non renseigné')}
								</Table.Cell>
								<Table.Cell class="px-3 py-3 text-right font-medium text-slate-900">
									{formatEur(bien.charges, '—')}
								</Table.Cell>
								{#if showActions}
									<Table.Cell class="px-3 py-3">
										<div class="flex justify-end gap-2">
											{#if onEdit}
												<Button
													type="button"
													size="sm"
													variant="outline"
													disabled={actionDisabled || busyRowId === String(bien.id || '')}
													aria-label={`Modifier ${bien.adresse}`}
													onclick={() => onEdit(bien)}
												>
													Modifier
												</Button>
											{/if}
											{#if onDelete}
												<Button
													type="button"
													size="sm"
													variant="destructive"
													disabled={actionDisabled || busyRowId === String(bien.id || '')}
													aria-label={`Supprimer ${bien.adresse}`}
													onclick={() => onDelete(bien)}
												>
													Supprimer
												</Button>
											{/if}
										</div>
									</Table.Cell>
								{/if}
							</Table.Row>
						{/each}
					</Table.Body>
				</Table.Root>
			</div>
		{/if}
	</CardContent>
</Card>
