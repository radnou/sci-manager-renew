<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Check, ArrowRight, Loader2 } from 'lucide-svelte';
	import { API_URL } from '$lib/api';
	import { supabase } from '$lib/supabase';

	let billingPeriod = $state<'month' | 'year'>('month');
	let checkoutLoading = $state<string | null>(null);
	let isAuthenticated = $state(false);

	$effect(() => {
		supabase.auth.getSession().then(({ data: { session } }) => {
			isAuthenticated = !!session;
		});
	});

	async function handlePlanClick(planKey: string, href: string | null) {
		if (href) {
			window.location.href = href;
			return;
		}
		checkoutLoading = planKey;
		try {
			const endpoint = isAuthenticated
				? `${API_URL}/api/v1/stripe/create-checkout`
				: `${API_URL}/api/v1/stripe/create-guest-checkout`;
			const headers: Record<string, string> = { 'Content-Type': 'application/json' };
			if (isAuthenticated) {
				const {
					data: { session }
				} = await supabase.auth.getSession();
				if (session) headers['Authorization'] = `Bearer ${session.access_token}`;
			}
			const res = await fetch(endpoint, {
				method: 'POST',
				headers,
				body: JSON.stringify({ plan_key: planKey, billing_period: billingPeriod })
			});
			const data = await res.json();
			if (data.url) {
				window.location.href = data.url;
			}
		} catch {
			window.location.href = '/register';
		} finally {
			checkoutLoading = null;
		}
	}

	const plans = [
		{
			key: 'free',
			name: 'Essentiel',
			description: 'Pour démarrer avec une petite SCI',
			monthlyPrice: 0,
			yearlyPrice: 0,
			popular: false,
			features: [
				'1 SCI',
				'2 biens maximum',
				'Suivi des loyers',
				'Suivi des charges',
				'Quittances PDF'
			],
			cta: 'Commencer gratuitement',
			href: '/register'
		},
		{
			key: 'starter',
			name: 'Gestion',
			description: 'Pour les gérants actifs avec plusieurs biens',
			monthlyPrice: 19,
			yearlyPrice: 180,
			popular: false,
			features: [
				'3 SCI',
				'10 biens maximum',
				'Gestion documentaire',
				'Notifications email',
				'Gestion des associés',
				'Assurance PNO & frais agence',
				'Support email prioritaire'
			],
			cta: 'Choisir Gestion',
			href: null
		},
		{
			key: 'pro',
			name: 'Fiscal',
			description: 'Pour les gestionnaires patrimoniaux exigeants',
			monthlyPrice: 39,
			yearlyPrice: 348,
			popular: true,
			features: [
				'SCI illimitées',
				'Biens illimités',
				'Calcul de rentabilité avancé',
				'Dashboard complet multi-SCI',
				'Résumé fiscal PDF (CERFA 2044)',
				'Tout Gestion inclus',
				'Support prioritaire dédié'
			],
			cta: 'Choisir Fiscal',
			href: null
		}
	];

	function formatPrice(plan: (typeof plans)[0]): string {
		if (plan.monthlyPrice === 0) return 'Gratuit';
		if (billingPeriod === 'month') return `${plan.monthlyPrice}€`;
		return `${plan.yearlyPrice}€`;
	}

	function formatPeriod(plan: (typeof plans)[0]): string {
		if (plan.monthlyPrice === 0) return '';
		if (billingPeriod === 'month') return '/mois';
		return '/an';
	}

	function formatPriceTTC(plan: (typeof plans)[0]): string | null {
		if (plan.monthlyPrice === 0) return null;
		const ht = billingPeriod === 'month' ? plan.monthlyPrice : plan.yearlyPrice;
		const ttc = (ht * 1.2).toFixed(2).replace('.', ',');
		const period = billingPeriod === 'month' ? '/mois' : '/an';
		return `(${ttc}€ TTC${period})`;
	}
</script>

<svelte:head>
	<title>Tarifs — GererSCI</title>
	<meta
		name="description"
		content="Comparez les offres GererSCI : Essentiel (gratuit), Gestion (19€/mois) et Fiscal (39€/mois)."
	/>
</svelte:head>

<section class="bg-slate-50 py-20 dark:bg-slate-950">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="mb-12 text-center">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Tarifs</Badge>
			<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
				Un prix simple, sans surprise
			</h2>
			<p class="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
				Commencez gratuitement, passez au plan supérieur quand vous en avez besoin.
			</p>

			<!-- Billing toggle -->
			<div
				class="mt-8 inline-flex items-center rounded-xl bg-white p-1 shadow-sm dark:bg-slate-800"
			>
				<button
					class="rounded-lg px-5 py-2 text-sm font-medium transition-colors {billingPeriod ===
					'month'
						? 'bg-blue-600 text-white shadow-sm'
						: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
					onclick={() => (billingPeriod = 'month')}
				>
					Mensuel
				</button>
				<button
					class="rounded-lg px-5 py-2 text-sm font-medium transition-colors {billingPeriod ===
					'year'
						? 'bg-blue-600 text-white shadow-sm'
						: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
					onclick={() => (billingPeriod = 'year')}
				>
					Annuel
					<span class="ml-1 text-xs font-normal opacity-80">-2 mois</span>
				</button>
			</div>
		</div>

		<div class="grid gap-8 md:grid-cols-3">
			{#each plans as plan}
				<div
					class="relative flex flex-col rounded-2xl border bg-white p-8 transition-shadow hover:shadow-lg dark:bg-slate-800 {plan.popular
						? 'border-blue-500 shadow-lg shadow-blue-500/10 dark:border-blue-400'
						: 'border-slate-200 dark:border-slate-700'}"
				>
					{#if plan.popular}
						<div class="absolute -top-3 left-1/2 -translate-x-1/2">
							<Badge
								class="bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-600"
							>
								Populaire
							</Badge>
						</div>
					{/if}

					<div class="mb-6">
						<h3 class="text-xl font-bold text-slate-900 dark:text-slate-100">
							{plan.name}
						</h3>
						<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
							{plan.description}
						</p>
					</div>

					<div class="mb-6">
						<span class="text-4xl font-extrabold text-slate-900 dark:text-white">
							{formatPrice(plan)}
						</span>
						{#if plan.monthlyPrice > 0}
							<span class="text-slate-500 dark:text-slate-400">
								HT{formatPeriod(plan)}
							</span>
							<div class="mt-1 text-sm text-slate-400 dark:text-slate-500">
								{formatPriceTTC(plan)}
							</div>
							{#if billingPeriod === 'year'}
								<div class="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
									Économisez 2 mois par rapport au mensuel
								</div>
							{/if}
						{/if}
					</div>

					<ul class="mb-8 flex-1 space-y-3">
						{#each plan.features as feat}
							<li class="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-400">
								<Check
									class="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600 dark:text-blue-400"
								/>
								<span>{feat}</span>
							</li>
						{/each}
					</ul>

					{#if plan.href}
						<a href={plan.href} class="mt-auto">
							<Button
								class="w-full {plan.popular
									? 'bg-blue-600 text-white hover:bg-blue-700'
									: ''}"
								variant={plan.popular ? 'default' : 'outline'}
								size="lg"
							>
								{plan.cta}
							</Button>
						</a>
					{:else}
						<Button
							class="mt-auto w-full {plan.popular
								? 'bg-blue-600 text-white hover:bg-blue-700'
								: ''}"
							variant={plan.popular ? 'default' : 'outline'}
							size="lg"
							disabled={checkoutLoading === plan.key}
							onclick={() => handlePlanClick(plan.key, plan.href)}
						>
							{#if checkoutLoading === plan.key}
								<Loader2 class="mr-2 h-4 w-4 animate-spin" />
								Redirection...
							{:else}
								{plan.cta}
							{/if}
						</Button>
					{/if}
				</div>
			{/each}
		</div>

		<div class="mt-12 text-center">
			<a
				href="/"
				class="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
			>
				<ArrowRight class="h-4 w-4 rotate-180" />
				Retour à l'accueil
			</a>
		</div>
	</div>
</section>
