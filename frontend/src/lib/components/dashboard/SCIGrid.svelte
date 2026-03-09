<script lang="ts">
	import type { SCIOverview } from '$lib/api';
	import type { SciScopeMetrics } from '$lib/high-value/portfolio';
	import { formatPercent } from '$lib/high-value/formatters';
	import { mapAssociateRoleLabel } from '$lib/high-value/presentation';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { Building2 } from 'lucide-svelte';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';

	type SciSnapshot = {
		sci: SCIOverview;
		bienMetrics: SciScopeMetrics['bienMetrics'];
		loyerMetrics: SciScopeMetrics['loyerMetrics'];
		biens: SciScopeMetrics['biens'];
		loyers: SciScopeMetrics['loyers'];
	};

	interface Props {
		snapshots: SciSnapshot[];
		activeSciId: string;
		loading: boolean;
		onSelect: (id: string) => void;
	}

	let { snapshots, activeSciId, loading, onSelect }: Props = $props();

	function statusLabel(status: SCIOverview['statut']) {
		if (!status) return 'À structurer';
		if (status === 'configuration') return 'À structurer';
		if (status === 'mise_en_service') return 'Mise en service';
		return 'En exploitation';
	}

	function statusClass(status: SCIOverview['statut']) {
		if (!status || status === 'configuration') {
			return 'bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-200';
		}
		if (status === 'mise_en_service') {
			return 'bg-cyan-100 text-cyan-900 dark:bg-cyan-950/40 dark:text-cyan-200';
		}
		return 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200';
	}

	function alertLabel(snapshot: SciSnapshot) {
		if (snapshot.loyerMetrics.lateCount > 0) return `${snapshot.loyerMetrics.lateCount} retard(s)`;
		if (snapshot.loyerMetrics.totalOutstanding > 0) return `${snapshot.loyerMetrics.totalOutstandingLabel} en attente`;
		if (snapshot.biens.length === 0) return 'Patrimoine à structurer';
		return 'Sous contrôle';
	}

	function alertClass(snapshot: SciSnapshot) {
		if (snapshot.loyerMetrics.lateCount > 0) return 'bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200';
		if (snapshot.loyerMetrics.totalOutstanding > 0) return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200';
		if (snapshot.biens.length === 0) return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200';
		return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200';
	}
</script>

<Card class="sci-section-card">
	<CardHeader>
		<CardTitle class="text-lg">Portefeuille multi-SCI</CardTitle>
		<CardDescription>
			Toutes les SCI accessibles par le compte. Cliquez sur une carte pour la rendre active.
		</CardDescription>
	</CardHeader>
	<CardContent class="pt-0">
		{#if loading}
			<div class="grid gap-3 lg:grid-cols-2">
				{#each Array.from({ length: 4 }) as _}
					<div class="h-40 animate-pulse rounded-3xl bg-slate-100 dark:bg-slate-900"></div>
				{/each}
			</div>
		{:else if snapshots.length === 0}
			<EmptyState
				icon={Building2}
				title="Créez votre première SCI en 2 minutes"
				description="Le dashboard portefeuille s'activera dès qu'une société sera liée à votre compte."
				actions={[{ label: 'Créer une SCI', href: '/scis' }]}
			/>
		{:else}
			<div class="grid gap-3 lg:grid-cols-2">
				{#each snapshots as snapshot (String(snapshot.sci.id))}
					<button
						type="button"
						class={`w-full rounded-[1.6rem] border p-4 text-left transition-colors ${
							String(snapshot.sci.id) === activeSciId
								? 'border-slate-900 bg-slate-900 text-white dark:border-slate-100 dark:bg-slate-100 dark:text-slate-950'
								: 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700'
						}`}
						aria-pressed={String(snapshot.sci.id) === activeSciId}
						onclick={() => onSelect(String(snapshot.sci.id))}
					>
						<div class="flex items-start justify-between gap-3">
							<div>
								<p class="text-sm font-semibold">{snapshot.sci.nom}</p>
								<p class="mt-1 text-xs opacity-75">SIREN {snapshot.sci.siren || 'À compléter'}</p>
								<p class="mt-2 text-xs opacity-80">
									{snapshot.sci.user_role
										? `${mapAssociateRoleLabel(snapshot.sci.user_role)} connecté`
										: 'Rôle utilisateur à confirmer'}
								</p>
							</div>
							<span class={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ${statusClass(snapshot.sci.statut)}`}>
								{statusLabel(snapshot.sci.statut)}
							</span>
						</div>
						<div class="mt-4 grid grid-cols-3 gap-2 text-xs">
							<div>
								<p class="font-semibold">{snapshot.bienMetrics.count}</p>
								<p class="opacity-75">Biens</p>
							</div>
							<div>
								<p class="font-semibold">{snapshot.bienMetrics.totalMonthlyRentLabel}</p>
								<p class="opacity-75">Loyer cible</p>
							</div>
							<div>
								<span class={`inline-flex rounded-full px-2 py-1 font-semibold ${alertClass(snapshot)}`}>
									{alertLabel(snapshot)}
								</span>
							</div>
						</div>
					</button>
				{/each}
			</div>
		{/if}
	</CardContent>
</Card>
