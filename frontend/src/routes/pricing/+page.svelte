<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Check, ArrowRight, Loader2 } from 'lucide-svelte';
	import { API_URL } from '$lib/api';
	import { supabase } from '$lib/supabase';
	import { addToast } from '$lib/components/ui/toast';

	let billingPeriod = $state<'month' | 'year'>('month');
	let checkoutLoading = $state<string | null>(null);
	let isAuthenticated = $state(false);
	let checkoutError = $state<string | null>(null);

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
		checkoutError = null;
		checkoutLoading = planKey;
		try {
			const endpoint = isAuthenticated
				? `${API_URL}/api/v1/stripe/create-checkout-session`
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

			let data: { url?: string; detail?: string; message?: string; error?: string } = {};
			try {
				data = await res.json();
			} catch {
				data = {};
			}

			if (!res.ok) {
				const message =
					res.status === 503
						? 'Le checkout Stripe est temporairement indisponible. Réessayez dans quelques minutes ou contactez le support.'
						: data.detail ?? data.message ?? data.error ?? "Impossible d'ouvrir le tunnel de souscription.";
				throw new Error(message);
			}

			if (data.url) {
				window.location.href = data.url;
				return;
			}
			throw new Error("L'URL de paiement est indisponible.");
		} catch (err: any) {
			const message = err?.message ?? "Impossible d'ouvrir le tunnel de souscription.";
			checkoutError = message;
			addToast({
				title: 'Paiement indisponible',
				description: message,
				variant: 'error',
				timeoutMs: 6000
			});
		} finally {
			checkoutLoading = null;
		}
	}

	const plans = [
		{
			key: 'free',
			name: 'Essentiel',
			description: 'Découvrez la gestion SCI simplifiée',
			monthlyPrice: 0,
			yearlyPrice: 0,
			popular: false,
			annualSavings: null,
			features: [
				'1 SCI',
				'1 bien',
				'Suivi des loyers',
				'Quittances PDF (filigrane)',
				'Simulateurs gratuits',
				'Calendrier fiscal (vue)'
			],
			cta: 'Commencer gratuitement',
			href: '/register'
		},
		{
			key: 'starter',
			name: 'Gestion',
			description: 'Automatisez votre gestion locative',
			monthlyPrice: 14,
			yearlyPrice: 108,
			popular: false,
			annualSavings: '60€',
			features: [
				'2 SCI',
				'5 biens',
				'Quittances PDF',
				'Relance impayé automatique',
				'Révision IRL',
				'Export CSV',
				'Support email 48h'
			],
			cta: 'Essayer 14 jours gratuit',
			href: null
		},
		{
			key: 'pro',
			name: 'Fiscal',
			description: 'Votre co-pilote fiscal et juridique',
			monthlyPrice: 34,
			yearlyPrice: 288,
			popular: true,
			annualSavings: '120€',
			features: [
				'5 SCI',
				'15 biens',
				'Résumé fiscal CERFA 2044',
				'Déficit foncier 10 ans',
				'Report 2042 par associé',
				'AG modèles + convocations',
				'Mouvements de parts',
				'Moteur 44+ échéances',
				'Calendrier fiscal interactif',
				'Tout Gestion inclus',
				'Support email 24h'
			],
			cta: 'Essayer 14 jours gratuit',
			href: null
		},
		{
			key: 'cabinet',
			name: 'Cabinet',
			description: "La puissance d'un cabinet, en autonomie",
			monthlyPrice: 69,
			yearlyPrice: 588,
			popular: false,
			annualSavings: '240€',
			features: [
				'SCI illimitées',
				'Biens illimités',
				'Multi-régime IR/IS',
				'Dissolution SCI',
				'Cession biens + plus-value',
				'Congé bailleur/locataire',
				'Avenant bail',
				'Export comptable complet',
				'Tout Fiscal inclus',
				'Support prioritaire'
			],
			cta: 'Essayer 14 jours gratuit',
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
	<title>Tarifs — GérerSCI</title>
	<meta
		name="description"
		content="Comparez les offres GérerSCI : Essentiel (gratuit), Gestion (14€/mois), Fiscal (34€/mois) et Cabinet (69€/mois)."
	/>
	<link rel="canonical" href="https://gerersci.fr/pricing" />
	<meta property="og:url" content="https://gerersci.fr/pricing" />
</svelte:head>

<section class="bg-slate-50 py-20 dark:bg-slate-950">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="mb-12 text-center">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Tarifs</Badge>
			<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
				Un prix simple, sans surprise
			</h2>
			<p class="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
				Chaque SCI mérite un co-pilote. Choisissez le vôtre.
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
					<span class="ml-1 text-xs font-normal opacity-80">jusqu'à -35%</span>
				</button>
			</div>

			{#if checkoutError}
				<div class="mx-auto mt-6 max-w-2xl rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-left text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-300">
					<p class="font-medium">Paiement temporairement indisponible</p>
					<p class="mt-1">{checkoutError}</p>
				</div>
			{/if}
		</div>

		<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
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
							{#if billingPeriod === 'year' && plan.annualSavings}
								<div class="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
									Économisez {plan.annualSavings}/an
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

		<p class="mt-10 text-center text-sm text-slate-500 dark:text-slate-400">
			Remplace en moyenne 150€/mois d'honoraires comptables
		</p>

		<div class="mt-8 text-center">
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
