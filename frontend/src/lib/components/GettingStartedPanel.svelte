<script lang="ts">
	import {
		Building2,
		FileText,
		HandCoins,
		Home,
		Landmark,
		ReceiptText,
		Users
	} from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import {
		buildOperatorOnboardingSteps,
		type OperatorOnboardingScope
	} from '$lib/onboarding/operator-steps';

	export let loading = false;
	export let sciCount = 0;
	export let associeCount = 0;
	export let bienCount = 0;
	export let loyerCount = 0;
	export let locataireCount = 0;
	export let chargeCount = 0;
	export let fiscaliteCount = 0;
	export let activeSciLabel = '';
	export let scope: OperatorOnboardingScope = 'all';
	export let compact = false;
	export let onDismiss: (() => void) | undefined = undefined;

	$: steps = [
		...buildOperatorOnboardingSteps(
			{
				sciCount,
				associeCount,
				bienCount,
				locataireCount,
				loyerCount,
				chargeCount,
				fiscaliteCount,
				activeSciLabel
			},
			scope
		)
	];
	$: completedSteps = steps.filter((step) => step.done).length;
	const entityGuide = [
		{
			title: 'SCI',
			icon: Building2,
			fields: 'Nom, SIREN, régime fiscal, statut, gouvernance, capacité et SCI active'
		},
		{
			title: 'Associé',
			icon: Users,
			fields: 'Nom, email, part détenue, rôle, membre compte ou gouvernance externe'
		},
		{
			title: 'Bien',
			icon: Home,
			fields: 'Adresse, ville, code postal, type locatif, loyer CC, charges, TMI, acquisition'
		},
		{
			title: 'Locataire',
			icon: Users,
			fields: 'Nom ou référence locataire, email, dates d’occupation, bien rattaché'
		},
		{
			title: 'Loyer',
			icon: ReceiptText,
			fields: 'Bien, locataire, date de loyer, montant, statut, quittance PDF'
		},
		{
			title: 'Charge',
			icon: HandCoins,
			fields: 'Bien support, type de charge, montant, date de paiement, journal exploitable'
		},
		{
			title: 'Fiscalité',
			icon: Landmark,
			fields: 'Année, revenus, charges, résultat fiscal recalculé, lecture consolidée'
		}
	];
</script>

<Card class="sci-section-card overflow-hidden">
	<CardHeader class="border-b border-slate-200/80 bg-slate-50/80 dark:border-slate-800 dark:bg-slate-900/80">
		<div class="flex flex-wrap items-start justify-between gap-4">
			<div>
				<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">
					{compact ? 'Cap suivant • parcours guidé' : 'Première connexion • prise en main guidée'}
				</p>
				<CardTitle class="mt-2 text-2xl">
					{compact ? 'Priorités de mise en route' : 'Débuter la gestion sans tâtonner'}
				</CardTitle>
				<CardDescription class="mt-2 max-w-3xl text-sm leading-7">
					{#if compact}
						Le hub te ramène sur les prochaines étapes réellement attendues dans cette zone de travail.
					{:else}
						Les solutions de gestion performantes poussent toujours un parcours simple: structurer le
						portefeuille, rattacher les actifs, renseigner les occupants, puis activer les flux et les
						documents. On garde ce fil ici.
					{/if}
				</CardDescription>
			</div>
			<div class="flex items-center gap-3">
				<div class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">
						Progression
					</p>
					<p class="mt-1 font-semibold text-slate-900 dark:text-slate-100">
						{completedSteps}/{steps.length} étapes
					</p>
				</div>
				{#if onDismiss}
					<Button type="button" variant="outline" size="sm" onclick={onDismiss}>
						Masquer
					</Button>
				{/if}
			</div>
		</div>
	</CardHeader>
	<CardContent class="grid gap-6 p-6 xl:grid-cols-[1.35fr_1fr]">
		{#if loading}
			<div class="space-y-3">
				{#each Array.from({ length: 4 }) as _, index (index)}
					<div class="h-28 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
				{/each}
			</div>
			<div class="grid gap-3 md:grid-cols-2 xl:grid-cols-1">
				{#each Array.from({ length: 4 }) as _, index (index)}
					<div class="h-28 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900"></div>
				{/each}
			</div>
		{:else}
			<div class="space-y-3">
				{#each steps as step (step.key)}
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
						<div class="flex items-start justify-between gap-3">
							<div>
								<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">{step.title}</p>
								<p class="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
									{step.description}
								</p>
							</div>
							<span
								class={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ${
									step.done
										? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200'
										: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-200'
								}`}
							>
								{step.done ? 'OK' : 'À faire'}
							</span>
						</div>
						<div class="mt-4 flex flex-wrap gap-2">
							<a href={step.href}>
								<Button size="sm" variant={step.done ? 'outline' : 'default'}>
									{step.actionLabel}
								</Button>
							</a>
						</div>
					</div>
				{/each}
			</div>

			{#if !compact}
				<div class="space-y-3">
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
						<div class="flex items-center gap-2 text-slate-500 dark:text-slate-400">
							<FileText class="h-4 w-4" />
							<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase">
								Référentiel des entités
							</p>
						</div>
						<p class="mt-3 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
							Chaque écran métier reprend ce découpage. Tu sais ainsi où créer, où contrôler et où
							documenter.
						</p>
					</div>
					<div class="grid gap-3 md:grid-cols-2 xl:grid-cols-2">
						{#each entityGuide as entity (entity.title)}
							<div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
								<div class="flex items-center gap-2 text-slate-900 dark:text-slate-100">
									<svelte:component this={entity.icon} class="h-4 w-4 text-cyan-600" />
									<p class="text-sm font-semibold">{entity.title}</p>
								</div>
								<p class="mt-3 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
									{entity.fields}
								</p>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</CardContent>
</Card>
