<script lang="ts">
	import {
		Building2,
		FileText,
		Home,
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

	export let loading = false;
	export let sciCount = 0;
	export let bienCount = 0;
	export let loyerCount = 0;
	export let locataireCount = 0;
	export let activeSciLabel = '';
	export let onDismiss: (() => void) | undefined = undefined;

	$: steps = [
		{
			key: 'sci',
			title: sciCount > 0 ? 'SCI structurée' : 'Créer ou sélectionner la première SCI',
			description:
				sciCount > 0
					? `${sciCount} SCI disponible(s). ${activeSciLabel ? `Active: ${activeSciLabel}.` : ''}`
					: 'Commence par ouvrir le portefeuille SCI et renseigner nom, SIREN, régime fiscal et associés.',
			href: '/scis',
			actionLabel: sciCount > 0 ? 'Ouvrir le portefeuille SCI' : 'Créer / sélectionner ma SCI',
			done: sciCount > 0
		},
		{
			key: 'bien',
			title: bienCount > 0 ? 'Premier bien rattaché' : 'Ajouter le premier bien',
			description:
				bienCount > 0
					? `${bienCount} bien(s) rattaché(s). Vérifie adresse, type locatif, loyer et charges.`
					: 'Rattache ensuite un actif immobilier à la SCI active avec ses caractéristiques métier.',
			href: '/biens',
			actionLabel: bienCount > 0 ? 'Contrôler les biens' : 'Ajouter mon premier bien',
			done: bienCount > 0
		},
		{
			key: 'locataire',
			title: locataireCount > 0
				? 'Locataire de référence renseigné'
				: 'Renseigner le premier locataire',
			description:
				locataireCount > 0
					? `${locataireCount} locataire(s) sont déjà documentés avec leur bien et leur période d’occupation.`
					: 'Passe dans Locataires pour rattacher la première personne au bon bien avec ses dates d’occupation.',
			href: '/locataires',
			actionLabel: locataireCount > 0 ? 'Voir les locataires' : 'Ajouter mon premier locataire',
			done: locataireCount > 0
		},
		{
			key: 'loyer',
			title: loyerCount > 0 ? 'Premier loyer saisi' : 'Saisir le premier loyer',
			description:
				loyerCount > 0
					? `${loyerCount} flux locatif(s) documenté(s). Tu peux produire les quittances.`
					: 'Documente ensuite le premier encaissement pour activer le journal, le recouvrement et les PDF.',
			href: '/loyers',
			actionLabel: loyerCount > 0 ? 'Suivre les loyers' : 'Saisir mon premier loyer',
			done: loyerCount > 0
		}
	];
	$: completedSteps = steps.filter((step) => step.done).length;
	const entityGuide = [
		{
			title: 'SCI',
			icon: Building2,
			fields: 'Nom, SIREN, régime fiscal, statut, associés, rôle utilisateur'
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
			title: 'Flux & docs',
			icon: ReceiptText,
			fields: 'Date, montant, statut, quittance PDF, charges documentées, clôture fiscale'
		}
	];
</script>

<Card class="sci-section-card overflow-hidden">
	<CardHeader class="border-b border-slate-200/80 bg-slate-50/80 dark:border-slate-800 dark:bg-slate-900/80">
		<div class="flex flex-wrap items-start justify-between gap-4">
			<div>
				<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">
					Première connexion • prise en main guidée
				</p>
				<CardTitle class="mt-2 text-2xl">Démarrer le cockpit sans tâtonner</CardTitle>
				<CardDescription class="mt-2 max-w-3xl text-sm leading-7">
					Les solutions de gestion performantes poussent toujours un parcours simple: structurer le
					portefeuille, rattacher les actifs, renseigner les occupants, puis activer les flux et les
					documents. On garde ce fil ici.
				</CardDescription>
			</div>
			<div class="flex items-center gap-3">
				<div class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-slate-500">
						Progression
					</p>
					<p class="mt-1 font-semibold text-slate-900 dark:text-slate-100">{completedSteps}/4 étapes</p>
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
				<div class="grid gap-3 md:grid-cols-2 xl:grid-cols-1">
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
	</CardContent>
</Card>
