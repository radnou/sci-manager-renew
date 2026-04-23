<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Check } from 'lucide-svelte';

	const valueStack = [
		{ item: 'Gestion locative complète', value: '25€/mois' },
		{ item: 'Quittances PDF conformes', value: '10€/mois' },
		{ item: 'Module fiscal CERFA 2044', value: '80€/mois' },
		{ item: 'Suivi charges et PNO', value: '20€/mois' },
		{ item: 'Calcul de rentabilité', value: '50€/mois' },
		{ item: 'Registre AG + convocations', value: '40€/mois' },
		{ item: 'Mouvements de parts', value: '30€/mois' },
		{ item: 'Calendrier fiscal + échéances', value: '17€/mois' },
		{ item: 'Notifications intelligentes', value: '10€/mois' },
		{ item: 'Tableau de bord multi-SCI', value: '30€/mois' },
		{ item: 'Import/Export données', value: '15€/mois' }
	];
</script>

<section class="bg-white py-20 dark:bg-slate-900">
	<div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
		<div class="mb-12 text-center">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Valeur</Badge>
			<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
				Tout ce que vous recevez
			</h2>
			<p class="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
				Chaque module remplace un outil ou un prestataire que vous payez déjà.
			</p>
		</div>

		<div class="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-700">
			<table class="w-full">
				<thead>
					<tr class="bg-slate-50 dark:bg-slate-800">
						<th class="px-6 py-4 text-left text-sm font-semibold text-slate-900 dark:text-slate-100">Ce que vous recevez</th>
						<th class="px-6 py-4 text-right text-sm font-semibold text-slate-900 dark:text-slate-100">Valeur équivalente</th>
					</tr>
				</thead>
				<tbody>
					{#each valueStack as row, i}
						<tr class="{i % 2 === 0 ? 'bg-white dark:bg-slate-900' : 'bg-slate-50/50 dark:bg-slate-800/50'}">
							<td class="px-6 py-3 text-sm text-slate-600 dark:text-slate-400">
								<span class="flex items-center gap-2">
									<Check class="h-4 w-4 flex-shrink-0 text-emerald-500" />
									{row.item}
								</span>
							</td>
							<td class="px-6 py-3 text-right text-sm text-slate-500 line-through dark:text-slate-400">{row.value}</td>
						</tr>
					{/each}
				</tbody>
				<tfoot>
					<tr class="border-t-2 border-slate-300 bg-slate-50 dark:border-slate-600 dark:bg-slate-800">
						<td class="px-6 py-4 text-sm font-bold text-slate-900 dark:text-slate-100">Total</td>
						<td class="px-6 py-4 text-right text-lg font-bold text-slate-400 line-through dark:text-slate-500">327€/mois</td>
					</tr>
					<tr class="bg-blue-50 dark:bg-blue-950/30">
						<td class="px-6 py-4 text-sm font-bold text-blue-700 dark:text-blue-300">Votre prix avec GérerSCI</td>
						<td class="px-6 py-4 text-right text-2xl font-extrabold text-blue-600 dark:text-blue-400">19€/mois</td>
					</tr>
				</tfoot>
			</table>
		</div>

		<p class="mt-6 text-center text-sm leading-relaxed text-slate-600 dark:text-slate-400">
			Vous payeriez plus de 320€ par mois pour assembler tous ces services séparément. Avec GérerSCI, vous avez tout — pour 19€ par mois.
		</p>
	</div>
</section>
