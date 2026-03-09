<script lang="ts">
	import type { SCIDetail, SCIOverview } from '$lib/api';
	import { Landmark, Users, ShieldCheck, TriangleAlert } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent } from '$lib/components/ui/card';
	import { formatEur, formatPercent } from '$lib/high-value/formatters';
	import { mapAssociateRoleLabel } from '$lib/high-value/presentation';

	interface CommandTrack {
		id: string;
		label: string;
		summary: string;
		detail: string;
	}

	interface Priority {
		title: string;
		description: string;
		tone: string;
	}

	interface Props {
		activeSciProfile: SCIDetail | SCIOverview | null;
		scis: SCIOverview[];
		activeSciId: string;
		collectionRate: number;
		avgAssociateShare: number;
		loyerMetrics: { lateCount: number; totalOutstanding: number; totalOutstandingLabel: string };
		commandTracks: CommandTrack[];
		priorities: Priority[];
		onSciChange: (id: string) => void;
	}

	let {
		activeSciProfile,
		scis,
		activeSciId,
		collectionRate,
		avgAssociateShare,
		loyerMetrics,
		commandTracks,
		priorities,
		onSciChange
	}: Props = $props();

	function statusLabel(status: SCIOverview['statut'] | null | undefined) {
		if (!status || status === 'configuration') return 'À structurer';
		if (status === 'mise_en_service') return 'Mise en service';
		return 'En exploitation';
	}

	function statusClass(status: SCIOverview['statut'] | null | undefined) {
		if (!status || status === 'configuration')
			return 'bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-200';
		if (status === 'mise_en_service')
			return 'bg-cyan-100 text-cyan-900 dark:bg-cyan-950/40 dark:text-cyan-200';
		return 'bg-emerald-100 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200';
	}
</script>

<Card class="sci-section-card overflow-hidden">
	<CardContent class="relative p-0">
		<div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-cyan-500 via-sky-400 to-emerald-500"></div>
		<div class="grid gap-6 p-6 lg:grid-cols-[1.4fr_1fr]">
			<div class="space-y-5">
				<div class="flex flex-wrap items-start justify-between gap-4">
					<div class="space-y-3">
						<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">SCI active</p>
						<div class="flex flex-wrap items-center gap-2">
							<span class={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusClass(activeSciProfile?.statut)}`}>
								{statusLabel(activeSciProfile?.statut)}
							</span>
							<span class="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
								Régime {activeSciProfile?.regime_fiscal || 'IR'}
							</span>
						</div>
						<h2 class="text-3xl font-semibold tracking-tight text-slate-950 dark:text-slate-50">
							{activeSciProfile?.nom || 'SCI à sélectionner'}
						</h2>
						<p class="max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
							{#if activeSciProfile}
								Lecture d'exécution de la SCI sélectionnée: identité, gouvernance, encaissements et documents à produire.
							{:else}
								Sélectionnez une SCI depuis la vue portefeuille pour ouvrir le détail d'exécution.
							{/if}
						</p>
					</div>

					{#if scis.length > 1}
						<label class="sci-field min-w-[16rem]">
							<span class="sci-field-label">Basculer la SCI active</span>
							<select
								class="sci-select"
								value={activeSciId}
								onchange={(e) => onSciChange((e.target as HTMLSelectElement).value)}
								aria-label="SCI active"
							>
								{#each scis as sci (String(sci.id))}
									<option value={String(sci.id)}>{sci.nom}</option>
								{/each}
							</select>
						</label>
					{/if}
				</div>

				<div class="grid gap-3 sm:grid-cols-3">
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
						<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
							<Landmark class="h-4 w-4" />
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Identité</p>
						</div>
						<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
							SIREN {activeSciProfile?.siren || 'À compléter'}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							{activeSciProfile?.user_role
								? `${mapAssociateRoleLabel(activeSciProfile.user_role)} connecté`
								: 'Rôle utilisateur à confirmer'}
						</p>
					</div>

					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
						<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
							<Users class="h-4 w-4" />
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Gouvernance</p>
						</div>
						<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
							{activeSciProfile?.associes_count || 0} associé(s)
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							Part moyenne {formatPercent(avgAssociateShare, 'N/A')}
						</p>
					</div>

					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
						<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
							<ShieldCheck class="h-4 w-4" />
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Santé SCI active</p>
						</div>
						<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
							Recouvrement {formatPercent(collectionRate, '0%')}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							{loyerMetrics.lateCount > 0
								? `${loyerMetrics.lateCount} ligne(s) à traiter`
								: loyerMetrics.totalOutstanding > 0
									? `${loyerMetrics.totalOutstandingLabel} restent à sécuriser`
									: 'Aucun retard détecté'}
						</p>
					</div>
				</div>
			</div>

			<div class="rounded-[1.5rem] border border-slate-200 bg-slate-50/90 p-5 dark:border-slate-700 dark:bg-slate-900">
				<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
					<TriangleAlert class="h-4 w-4" />
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">Postes de pilotage</p>
				</div>
				<p class="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
					Chaque bloc ci-dessous renvoie vers une zone du cockpit.
				</p>
				<div class="mt-4 space-y-3">
					{#each commandTracks as track}
						<a
							href={`#${track.id}`}
							class="group block rounded-2xl border border-slate-200 bg-white p-4 transition-colors hover:border-slate-300 dark:border-slate-700 dark:bg-slate-950 dark:hover:border-slate-600"
						>
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">{track.label}</p>
									<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{track.summary}</p>
									<p class="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{track.detail}</p>
								</div>
								<span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-700 transition-colors group-hover:bg-slate-900 group-hover:text-white dark:bg-slate-800 dark:text-slate-200 dark:group-hover:bg-slate-100 dark:group-hover:text-slate-950">
									Voir
								</span>
							</div>
						</a>
					{/each}
				</div>
				<div class="mt-5">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-slate-500 uppercase">À traiter maintenant</p>
				</div>
				<div class="mt-3 space-y-3">
					{#each priorities as item}
						<div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
							<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">{item.title}</p>
							<p class="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{item.description}</p>
						</div>
					{/each}
				</div>
				<div class="mt-4 flex flex-wrap gap-2">
					<a href="/scis"><Button variant="outline" size="sm">Voir les SCI</Button></a>
					<a href="/biens"><Button size="sm">Gérer les biens</Button></a>
					<a href="/loyers"><Button variant="outline" size="sm">Suivre les loyers</Button></a>
				</div>
			</div>
		</div>
	</CardContent>
</Card>
