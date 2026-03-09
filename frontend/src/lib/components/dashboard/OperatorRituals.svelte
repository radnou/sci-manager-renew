<script lang="ts">
	import type { Loyer, Bien, Charge, Fiscalite } from '$lib/api';
	import { FileText } from 'lucide-svelte';
	import { formatEur, formatFrDate } from '$lib/high-value/formatters';
	import { mapLoyerStatusLabel } from '$lib/high-value/loyers';
	import { mapChargeTypeLabel } from '$lib/high-value/presentation';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';

	interface Props {
		latestLoyer: Loyer | null;
		scopedLoyers: Loyer[];
		monthlyPropertyCharges: number;
		latestFiscalYear: Fiscalite | null;
		latestCharge: Charge | null;
	}

	let { latestLoyer, scopedLoyers, monthlyPropertyCharges, latestFiscalYear, latestCharge }: Props = $props();
</script>

<Card class="sci-section-card">
	<CardHeader>
		<CardTitle class="flex items-center gap-2 text-lg">
			<FileText class="h-5 w-5 text-sky-600" />
			Rituels opérateur
		</CardTitle>
		<CardDescription>
			Repères desktop pour la revue hebdomadaire, la quittance et la clôture.
		</CardDescription>
	</CardHeader>
	<CardContent class="space-y-4">
		<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Dernier flux locatif</p>
			<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
				{latestLoyer
					? `${formatFrDate(latestLoyer.date_loyer)} • ${formatEur(latestLoyer.montant)}`
					: 'Aucun flux saisi'}
			</p>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
				{latestLoyer ? mapLoyerStatusLabel(latestLoyer.statut) : 'Le journal locatif s\'activera dès la première saisie.'}
			</p>
		</div>
		<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Cadence documentaire</p>
			<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
				{scopedLoyers.length > 0 ? 'Quittances générables immédiatement' : 'Aucune quittance à produire'}
			</p>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
				{scopedLoyers.length > 0
					? `${scopedLoyers.length} loyer(s) saisi(s) sur la SCI active.`
					: 'Le module PDF attend au moins un loyer enregistré.'}
			</p>
		</div>
		<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Charges récurrentes</p>
			<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{formatEur(monthlyPropertyCharges)}</p>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">charges mensuelles renseignées sur les biens de la SCI active.</p>
		</div>
		<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
			<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">Clôture fiscale</p>
			<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
				{latestFiscalYear ? `Exercice ${latestFiscalYear.annee}` : 'Aucun exercice consolidé'}
			</p>
			<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
				{latestCharge
					? `${mapChargeTypeLabel(latestCharge.type_charge)} • payée le ${formatFrDate(latestCharge.date_paiement)}`
					: 'Aucune charge récente documentée.'}
			</p>
		</div>
	</CardContent>
</Card>
