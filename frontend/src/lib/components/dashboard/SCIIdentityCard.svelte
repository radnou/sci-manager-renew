<script lang="ts">
	import type { SCIDetail, SCIOverview, Bien } from '$lib/api';
	import { Landmark } from 'lucide-svelte';
	import { formatEur, formatPercent } from '$lib/high-value/formatters';
	import { mapAssociateRoleLabel } from '$lib/high-value/presentation';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';

	interface Props {
		activeSciProfile: SCIDetail | SCIOverview | null;
		activeSciDetail: SCIDetail | null;
		scopedBiens: Bien[];
		bienMetrics: { totalMonthlyRent: number };
		detailLoading: boolean;
	}

	let { activeSciProfile, activeSciDetail, scopedBiens, bienMetrics, detailLoading }: Props =
		$props();

	function statusLabel(status: SCIOverview['statut'] | null | undefined) {
		if (!status || status === 'configuration') return 'À structurer';
		if (status === 'mise_en_service') return 'Mise en service';
		return 'En exploitation';
	}
</script>

<Card class="sci-section-card">
	<CardHeader>
		<CardTitle class="flex items-center gap-2 text-lg">
			<Landmark class="h-5 w-5 text-sky-600" />
			Fiche d'identité SCI active
		</CardTitle>
		<CardDescription>Caractéristiques centrales de la société sélectionnée.</CardDescription>
	</CardHeader>
	<CardContent class="pt-0">
		{#if detailLoading}
			<div class="grid gap-3 md:grid-cols-2">
				{#each Array.from({ length: 4 }) as _}
					<div class="h-24 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
				{/each}
			</div>
		{:else}
			<div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
				<div
					class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
				>
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Société
					</p>
					<p class="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
						SIREN {activeSciProfile?.siren || 'À compléter'}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						{statusLabel(activeSciProfile?.statut)}
					</p>
				</div>
				<div
					class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
				>
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Gouvernance
					</p>
					<p class="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{activeSciProfile?.user_role
							? mapAssociateRoleLabel(activeSciProfile.user_role)
							: 'Rôle à confirmer'}
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Part détenue {formatPercent(activeSciProfile?.user_part, 'N/A')}
					</p>
				</div>
				<div
					class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
				>
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Patrimoine
					</p>
					<p class="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{activeSciDetail?.biens_count ?? scopedBiens.length} bien(s)
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Loyer cible {formatEur(
							activeSciDetail?.total_monthly_rent ?? bienMetrics.totalMonthlyRent
						)}
					</p>
				</div>
				<div
					class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
				>
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">
						Documentation
					</p>
					<p class="mt-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{activeSciDetail?.fiscalite?.length || 0} exercice(s)
					</p>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						{activeSciDetail?.charges_count ?? 0} charge(s) documentée(s)
					</p>
				</div>
			</div>
		{/if}
	</CardContent>
</Card>
