<script lang="ts">
	import { Building2, Home, HandCoins, FileText, ChevronRight, Check } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';

	interface Props {
		hasSci: boolean;
		hasBien: boolean;
		hasLoyer: boolean;
		hasQuittance: boolean;
	}

	let { hasSci, hasBien, hasLoyer, hasQuittance }: Props = $props();

	const steps = $derived([
		{
			label: 'Créer votre première SCI',
			description: 'Renseignez le nom, SIREN et régime fiscal de votre société.',
			icon: Building2,
			done: hasSci,
			href: '/scis'
		},
		{
			label: 'Ajouter un bien immobilier',
			description: 'Documentez votre premier actif avec adresse, type et loyer cible.',
			icon: Home,
			done: hasBien,
			href: '/biens'
		},
		{
			label: 'Enregistrer un loyer',
			description: 'Saisissez le premier encaissement pour activer le suivi.',
			icon: HandCoins,
			done: hasLoyer,
			href: '/loyers'
		},
		{
			label: 'Générer une quittance',
			description: 'Produisez votre première quittance PDF en un clic.',
			icon: FileText,
			done: hasQuittance,
			href: '/dashboard#dashboard-documents'
		}
	]);

	const completedCount = $derived(steps.filter((s) => s.done).length);
	const allDone = $derived(completedCount === steps.length);
	const progressPercent = $derived(Math.round((completedCount / steps.length) * 100));
</script>

{#if !allDone}
	<div
		class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950"
	>
		<div class="mb-4 flex items-center justify-between">
			<div>
				<h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Démarrage rapide</h3>
				<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
					{completedCount}/{steps.length} étapes complétées
				</p>
			</div>
			<div class="text-right">
				<span class="text-lg font-bold text-slate-900 dark:text-slate-100">{progressPercent}%</span>
			</div>
		</div>

		<div class="mb-4 h-1.5 w-full rounded-full bg-slate-100 dark:bg-slate-800">
			<div
				class="h-1.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
				style="width: {progressPercent}%"
			></div>
		</div>

		<div class="space-y-2">
			{#each steps as step, i}
				<a
					href={step.done ? undefined : step.href}
					class="flex items-center gap-3 rounded-xl border border-slate-200 p-3 transition-colors {step.done
						? 'border-emerald-200 bg-emerald-50/50 dark:border-emerald-800 dark:bg-emerald-950/20'
						: 'hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:hover:border-slate-700 dark:hover:bg-slate-900'}"
				>
					<div
						class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full {step.done
							? 'bg-emerald-500 text-white'
							: 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'}"
					>
						{#if step.done}
							<Check class="h-4 w-4" />
						{:else}
							<step.icon class="h-4 w-4" />
						{/if}
					</div>
					<div class="min-w-0 flex-1">
						<p
							class="text-sm font-medium {step.done
								? 'text-emerald-700 line-through dark:text-emerald-300'
								: 'text-slate-900 dark:text-slate-100'}"
						>
							{step.label}
						</p>
						{#if !step.done}
							<p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{step.description}</p>
						{/if}
					</div>
					{#if !step.done}
						<ChevronRight class="h-4 w-4 flex-shrink-0 text-slate-400" />
					{/if}
				</a>
			{/each}
		</div>
	</div>
{/if}
