<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchSubscriptionEntitlements, cancelSubscription, type SubscriptionEntitlements } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import { addToast } from '$lib/components/ui/toast';
	import { CreditCard, ExternalLink, ArrowLeft, AlertTriangle } from 'lucide-svelte';

	let subscription: SubscriptionEntitlements | null = $state(null);
	let loading = $state(true);
	let error = $state('');
	let cancelStep = $state(0); // 0=idle, 1=confirm, 2=processing
	let cancelError = $state('');

	function getCapacityLabel(sub: SubscriptionEntitlements): string {
		if (sub.max_scis == null) return 'SCI et biens illimités';
		return `${sub.current_scis}/${sub.max_scis} SCI · ${sub.current_biens}/${sub.max_biens} biens`;
	}

	async function handleCancel() {
		if (cancelStep === 0) {
			cancelStep = 1; // Show confirmation
			return;
		}
		if (cancelStep === 1) {
			cancelStep = 2; // Processing
			try {
				const result = await cancelSubscription();
				addToast({ title: result.message, variant: 'success' });
				cancelStep = 0;
				// Reload subscription data
				subscription = await fetchSubscriptionEntitlements();
			} catch (err) {
				cancelError = formatApiErrorMessage(err, 'Erreur lors de la résiliation.');
				cancelStep = 1;
			}
		}
	}

	onMount(async () => {
		try {
			subscription = await fetchSubscriptionEntitlements();
		} catch (err) {
			error = formatApiErrorMessage(err, "Impossible de charger l'abonnement.");
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head><title>Abonnement | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Compte · abonnement et facturation</p>
		<h1 class="sci-page-title">Mon abonnement</h1>
		<p class="sci-page-subtitle">
			Consultez votre offre active, vos quotas et gérez votre facturation.
		</p>
	</header>

	{#if loading}
		<div class="sci-loading" role="status" aria-label="Chargement"></div>
	{:else if error}
		<div class="sci-inline-alert sci-inline-alert-error" role="alert">{error}</div>
	{:else if subscription}
		<div class="grid gap-6 lg:grid-cols-2">
			<Card class="sci-section-card">
				<CardHeader>
					<div class="flex items-center gap-3">
						<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-100 dark:bg-sky-900/30">
							<CreditCard class="h-5 w-5 text-sky-600 dark:text-sky-400" />
						</div>
						<div>
							<CardTitle class="text-lg">Offre active</CardTitle>
							<CardDescription>Votre plan et ses limites</CardDescription>
						</div>
					</div>
				</CardHeader>
				<CardContent class="grid gap-4 pt-0">
					<div class="rounded-2xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900">
						<p class="sci-eyebrow">Plan actuel</p>
						<p class="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
							{subscription.plan_name}
						</p>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{getCapacityLabel(subscription)}</p>
					</div>

					<div class="grid gap-3 sm:grid-cols-2">
						<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
							<p class="sci-eyebrow">SCI</p>
							<p class="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
								{subscription.current_scis}{#if subscription.max_scis != null}<span class="text-sm font-normal text-slate-400"> / {subscription.max_scis}</span>{/if}
							</p>
						</div>
						<div class="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
							<p class="sci-eyebrow">Biens</p>
							<p class="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-100">
								{subscription.current_biens}{#if subscription.max_biens != null}<span class="text-sm font-normal text-slate-400"> / {subscription.max_biens}</span>{/if}
							</p>
						</div>
					</div>
				</CardContent>
			</Card>

			<Card class="sci-section-card">
				<CardHeader>
					<div>
						<CardTitle class="text-lg">Actions</CardTitle>
						<CardDescription>Gérez votre abonnement et votre facturation</CardDescription>
					</div>
				</CardHeader>
				<CardContent class="grid gap-3 pt-0">
					<Button href="/pricing" class="justify-start gap-2">
						<ExternalLink class="h-4 w-4" aria-hidden="true" />
						Changer d'offre
					</Button>
					<Button href="/account" variant="outline" class="justify-start gap-2">
						<ArrowLeft class="h-4 w-4" aria-hidden="true" />
						Retour au compte
					</Button>

					<!-- Résiliation en 3 clics (loi 16 août 2022) -->
					{#if subscription.is_active && subscription.status !== 'no_subscription'}
						<hr class="my-2 border-slate-200 dark:border-slate-700" />

						{#if cancelStep === 0}
							<Button
								variant="outline"
								class="justify-start gap-2 text-rose-600 hover:bg-rose-50 hover:text-rose-700 dark:text-rose-400 dark:hover:bg-rose-950"
								onclick={handleCancel}
							>
								<AlertTriangle class="h-4 w-4" aria-hidden="true" />
								Résilier mon abonnement
							</Button>
						{:else if cancelStep === 1}
							<div class="rounded-xl border border-rose-200 bg-rose-50 p-4 dark:border-rose-800 dark:bg-rose-950/30">
								<p class="text-sm font-medium text-rose-800 dark:text-rose-200">
									Confirmez la résiliation
								</p>
								<p class="mt-1 text-xs text-rose-600 dark:text-rose-400">
									Votre abonnement restera actif jusqu'à la fin de la période en cours.
									Vous conserverez l'accès à toutes les fonctionnalités jusqu'à cette date.
								</p>
								{#if cancelError}
									<p class="mt-2 text-xs font-medium text-rose-700" role="alert">{cancelError}</p>
								{/if}
								<div class="mt-3 flex gap-2">
									<Button
										variant="destructive"
										size="sm"
										onclick={handleCancel}
									>
										Confirmer la résiliation
									</Button>
									<Button
										variant="outline"
										size="sm"
										onclick={() => { cancelStep = 0; cancelError = ''; }}
									>
										Annuler
									</Button>
								</div>
							</div>
						{:else}
							<div class="flex items-center gap-2 text-sm text-slate-500">
								<div class="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-rose-500"></div>
								Résiliation en cours...
							</div>
						{/if}
					{/if}
				</CardContent>
			</Card>
		</div>
	{:else}
		<div class="sci-empty-state">
			<p>Aucun abonnement actif. Choisissez un plan pour accéder à GérerSCI.</p>
			<Button href="/pricing" class="mt-4">Choisir un plan</Button>
		</div>
	{/if}
</section>
