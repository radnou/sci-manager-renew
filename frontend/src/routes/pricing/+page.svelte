<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Check, ArrowRight, Loader2, Crown } from 'lucide-svelte';
	import { API_URL } from '$lib/api';
	import { supabase } from '$lib/supabase';
	import { addToast } from '$lib/components/ui/toast';

	let billingPeriod = $state<'month' | 'year'>('month');
	let checkoutLoading = $state<string | null>(null);
	let isAuthenticated = $state(false);
	let checkoutError = $state<string | null>(null);
	let consentRetractation = $state(false);

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
			key: 'starter',
			name: 'Gestion',
			description: 'Automatisez votre gestion locative',
			monthlyPrice: 19,
			yearlyPrice: 190,
			popular: false,
			features: [
				'1 SCI',
				'5 biens',
				'Quittances PDF conformes',
				'Suivi des loyers + relances auto',
				'Résumé fiscal CERFA 2044',
				'Charges, PNO, frais agence',
				'Export CSV',
				'Support email 48h'
			],
			cta: 'Démarrer pour 19€/mois',
			href: null
		},
		{
			key: 'pro',
			name: 'Pilotage',
			description: 'Votre co-pilote fiscal et juridique',
			monthlyPrice: 39,
			yearlyPrice: 390,
			popular: true,
			features: [
				'SCI illimitées',
				'Biens illimités',
				'Tout Gestion inclus',
				'Assemblées générales + convocations',
				'Mouvements de parts + simulation droits',
				'Moteur 44+ échéances',
				'Calendrier fiscal interactif',
				'Vue comptable annuelle',
				'Révision IRL automatique',
				'Support prioritaire 24h'
			],
			cta: 'Démarrer pour 39€/mois',
			href: null
		}
	];

	function formatPrice(plan: (typeof plans)[0]): string {
		if (billingPeriod === 'month') return `${plan.monthlyPrice}€`;
		return `${plan.yearlyPrice}€`;
	}

	function formatPeriod(): string {
		if (billingPeriod === 'month') return '/mois';
		return '/an';
	}

	function formatPriceTTC(plan: (typeof plans)[0]): string {
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
		content="Comparez les offres GérerSCI : Gestion (19€/mois) et Pilotage (39€/mois). Garanti 30 jours satisfait ou remboursé."
	/>
	<link rel="canonical" href="https://gerersci.fr/pricing" />
	<meta property="og:url" content="https://gerersci.fr/pricing" />
</svelte:head>

<section class="bg-slate-50 py-20 dark:bg-slate-950">
	<div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
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
					<span class="ml-1 text-xs font-normal opacity-80">2 mois offerts</span>
				</button>
			</div>

			{#if checkoutError}
				<div class="mx-auto mt-6 max-w-2xl rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-left text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-300">
					<p class="font-medium">Paiement temporairement indisponible</p>
					<p class="mt-1">{checkoutError}</p>
				</div>
			{/if}

			<label class="mx-auto mt-6 flex max-w-2xl cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm text-slate-600 transition-colors hover:border-blue-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:border-blue-600">
				<input
					type="checkbox"
					bind:checked={consentRetractation}
					class="mt-0.5 h-4 w-4 flex-shrink-0 rounded border-slate-300 text-blue-600 focus:ring-blue-500 dark:border-slate-600"
				/>
				<span>
					Conformément à l'article L221-28 du Code de la consommation, je souhaite accéder
					immédiatement au Service et je reconnais expressément <strong>renoncer à mon droit
					de rétractation de 14 jours</strong>. Je bénéficie de la
					<a href="/cgv#garantie" class="text-blue-600 underline hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">garantie satisfait ou remboursé de 30 jours</a>.
				</span>
			</label>
		</div>

		<div class="grid gap-8 md:grid-cols-2">
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
						<span class="text-slate-500 dark:text-slate-400">
							HT{formatPeriod()}
						</span>
						<div class="mt-1 text-sm text-slate-400 dark:text-slate-500">
							{formatPriceTTC(plan)}
						</div>
						{#if billingPeriod === 'year'}
							<div class="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
								2 mois offerts
							</div>
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

					<Button
						class="mt-auto w-full {plan.popular
							? 'bg-blue-600 text-white hover:bg-blue-700'
							: ''}"
						variant={plan.popular ? 'default' : 'outline'}
						size="lg"
						disabled={checkoutLoading === plan.key || !consentRetractation}
						onclick={() => handlePlanClick(plan.key, plan.href)}
					>
						{#if checkoutLoading === plan.key}
							<Loader2 class="mr-2 h-4 w-4 animate-spin" />
							Redirection...
						{:else}
							{plan.cta}
						{/if}
					</Button>

					<p class="mt-3 text-center text-xs text-slate-400 dark:text-slate-500">
						Paiement sécurisé · Garanti 30 jours satisfait ou remboursé · Annulation en 1 clic
					</p>
				</div>
			{/each}
		</div>

		<!-- Fondateur offer -->
		<div class="mt-12 rounded-2xl border-2 border-amber-400 bg-gradient-to-br from-amber-50 to-orange-50 p-8 dark:border-amber-500 dark:from-amber-950/30 dark:to-orange-950/30">
			<div class="flex flex-col items-center text-center lg:flex-row lg:text-left lg:items-start lg:gap-8">
				<div class="flex-1">
					<Badge class="mb-3 bg-amber-500 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-500">
						Offre de lancement — 25 places
					</Badge>
					<h3 class="text-2xl font-bold text-slate-900 dark:text-slate-100">
						<Crown class="mr-2 inline h-6 w-6 text-amber-500" />
						Fondateur
					</h3>
					<p class="mt-2 text-slate-600 dark:text-slate-400">
						Accès à vie au plan Pilotage
					</p>
					<ul class="mt-4 space-y-2">
						<li class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
							<Check class="h-4 w-4 flex-shrink-0 text-amber-500" />
							Tout Pilotage inclus — à vie
						</li>
						<li class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
							<Check class="h-4 w-4 flex-shrink-0 text-amber-500" />
							Ligne directe avec le fondateur
						</li>
						<li class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
							<Check class="h-4 w-4 flex-shrink-0 text-amber-500" />
							Accès beta aux nouvelles fonctionnalités
						</li>
					</ul>
				</div>
				<div class="mt-6 flex flex-col items-center lg:mt-0">
					<div class="text-5xl font-extrabold text-slate-900 dark:text-white">500€</div>
					<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
						Paiement unique. Pas de mensualité. À vie.
					</p>
					<Button
						size="lg"
						class="mt-4 w-full bg-amber-500 px-8 text-white hover:bg-amber-600"
						disabled={checkoutLoading === 'lifetime' || !consentRetractation}
						onclick={() => handlePlanClick('lifetime', null)}
					>
						{#if checkoutLoading === 'lifetime'}
							<Loader2 class="mr-2 h-4 w-4 animate-spin" />
							Redirection...
						{:else}
							Devenir Fondateur
						{/if}
					</Button>
					<p class="mt-3 text-sm font-medium text-amber-700 dark:text-amber-400">
						Places restantes sur 25
					</p>
				</div>
			</div>
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
