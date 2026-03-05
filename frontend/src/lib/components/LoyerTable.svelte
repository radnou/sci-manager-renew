<script lang="ts">
	import type { Bien, Loyer } from '$lib/api';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { mapLoyerStatusClass, mapLoyerStatusLabel } from '$lib/high-value/loyers';
	import * as Table from '$lib/components/ui/table';

	export let loyers: Loyer[] = [];
	export let biens: Pick<Bien, 'id' | 'adresse' | 'ville'>[] = [];
	export let loading = false;
	export let title = 'Journal des loyers';
	export let description = 'Historique chronologique des encaissements et montants.';

	function resolveBienLabel(idBien: Loyer['id_bien']) {
		const bien = biens.find((entry) => String(entry.id || '') === String(idBien || ''));
		if (!bien) {
			return 'Bien non identifié';
		}

		return bien.ville ? `${bien.adresse} • ${bien.ville}` : bien.adresse;
	}
</script>

<Card class="sci-section-card">
	<CardHeader class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
		<div>
			<CardTitle class="text-lg">{title}</CardTitle>
			<CardDescription>{description}</CardDescription>
		</div>
		<p class="text-xs font-semibold tracking-[0.2em] text-slate-500 uppercase">{loyers.length} enregistrements</p>
	</CardHeader>
	<CardContent class="pt-0">
		{#if loading}
			<div class="space-y-2" aria-live="polite">
				{#each Array.from({ length: 6 }) as _, index}
					<div class="h-11 animate-pulse rounded-md bg-slate-100" data-index={index}></div>
				{/each}
			</div>
		{:else if loyers.length === 0}
			<div class="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
				<p class="text-sm font-medium text-slate-700">Aucun loyer saisi.</p>
				<p class="mt-1 text-sm text-slate-500">Ajoute un paiement pour construire l’historique comptable.</p>
			</div>
		{:else}
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head class="px-3">Date</Table.Head>
						<Table.Head class="px-3">Bien</Table.Head>
						<Table.Head class="px-3">Statut</Table.Head>
						<Table.Head class="px-3 text-right">Montant</Table.Head>
					</Table.Row>
				</Table.Header>
					<Table.Body>
						{#each loyers as loyer}
							<Table.Row>
								<Table.Cell class="px-3 py-3 font-medium text-slate-900">{formatFrDate(loyer.date_loyer)}</Table.Cell>
								<Table.Cell class="px-3 py-3 text-slate-700">{resolveBienLabel(loyer.id_bien)}</Table.Cell>
								<Table.Cell class="px-3 py-3">
									<span class={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${mapLoyerStatusClass(loyer.statut)}`}>
										{mapLoyerStatusLabel(loyer.statut)}
									</span>
								</Table.Cell>
								<Table.Cell class="px-3 py-3 text-right font-medium text-slate-900">
									{formatEur(loyer.montant)}
								</Table.Cell>
							</Table.Row>
						{/each}
				</Table.Body>
			</Table.Root>
		{/if}
	</CardContent>
</Card>
