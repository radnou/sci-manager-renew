<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Check, ArrowRight, Loader2, Crown } from 'lucide-svelte';
	import { API_URL } from '$lib/api';
	import { supabase } from '$lib/supabase';
	import { addToast } from '$lib/components/ui/toast';
	import CheckoutConfirmModal from '$lib/components/CheckoutConfirmModal.svelte';
	import { trackEvent, EVENTS } from '$lib/analytics';
	import { PLANS_LIST, formatPrice, formatPeriod, formatPriceTTC } from '$lib/config/plans';

	let billingPeriod = $state<'month' | 'year'>('month');
	let checkoutLoading = $state<string | null>(null);
	let isAuthenticated = $state(false);
	let checkoutError = $state<string | null>(null);
	let modalOpen = $state(false);
	let modalPlanKey = $state('');
	let modalPlanName = $state('');
	let modalPlanPrice = $state('');
	let modalPlanPeriod = $state('');
	let modalPlanFeatures = $state<string[]>([]);

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

	function openCheckoutModal(planKey: string) {
		trackEvent(EVENTS.PRICING_PLAN_SELECT, { plan: planKey });

		// Anonymous → redirect to register
		if (!isAuthenticated) {
			window.location.href = `/register?plan=${planKey}`;
			return;
		}

		const plan = plans.find((p) => p.key === planKey);
		if (!plan) {
			// Handle lifetime separately
			if (planKey === 'lifetime') {
				modalPlanKey = 'lifetime';
				modalPlanName = 'Fondateur';
				modalPlanPrice = '500€';
				modalPlanPeriod = ' unique';
				modalPlanFeatures = [
					'Tout Pilotage inclus — à vie',
					'Ligne directe avec le fondateur',
					'Accès beta aux nouvelles fonctionnalités'
				];
				modalOpen = true;
			}
			return;
		}
		modalPlanKey = planKey;
		modalPlanName = plan.name;
		modalPlanPrice = billingPeriod === 'month' ? `${plan.monthlyPrice}€` : `${plan.yearlyPrice}€`;
		modalPlanPeriod = billingPeriod === 'month' ? '/mois' : '/an';
		modalPlanFeatures = plan.features;
		modalOpen = true;
	}

	function handleModalConfirm() {
		modalOpen = false;
		handlePlanClick(modalPlanKey, null);
	}

	const plans = PLANS_LIST;


</script>

<svelte:head>
	<title>Tarifs — GérerSCI</title>
	<meta
		name="description"
		content="Comparez les offres GérerSCI : Gestion (19€/mois) et Pilotage (39€/mois). Garanti 30 jours satisfait ou remboursé."
	/>
	<link rel="canonical" href="https://gerersci.fr/pricing" />
	<meta property="og:title" content="Tarifs — GérerSCI" />
	<meta property="og:description" content="Gestion 19€/mois, Pilotage 39€/mois. Garanti 30 jours satisfait ou remboursé." />
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://gerersci.fr/pricing" />
	<meta property="og:image" content="https://gerersci.fr/images/showcase/dashboard-light.png" />
</svelte:head>

<section class="bg-slate-50 py-20 dark:bg-slate-950">
	<div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
		<div class="mb-12 text-center">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Tarifs</Badge>
			<h1 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
				Un prix simple, sans surprise
			</h1>
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
					onclick={() => { billingPeriod = 'month'; trackEvent(EVENTS.BILLING_TOGGLE, { period: 'month' }); }}
				>
					Mensuel
				</button>
				<button
					class="rounded-lg px-5 py-2 text-sm font-medium transition-colors {billingPeriod ===
					'year'
						? 'bg-blue-600 text-white shadow-sm'
						: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'}"
					onclick={() => { billingPeriod = 'year'; trackEvent(EVENTS.BILLING_TOGGLE, { period: 'year' }); }}
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

			</div>

		<div class="mx-auto mt-10 mb-10 max-w-2xl rounded-xl border border-blue-200 bg-blue-50 p-6 dark:border-blue-900 dark:bg-blue-950/30">
			<p class="mb-3 text-sm font-semibold text-blue-800 dark:text-blue-300">Ce que GérerSCI remplace :</p>
			<ul class="space-y-2">
				{#each ['Suivi des loyers et alertes impayés automatiques', 'Génération de quittances PDF en 1 clic', 'Pré-remplissage CERFA 2044 automatique', 'Vue financière consolidée multi-SCI'] as item}
					<li class="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-400">
						<Check class="h-4 w-4 flex-shrink-0 text-blue-500" />
						{item}
					</li>
				{/each}
			</ul>
			<p class="mt-3 text-xs text-blue-600 dark:text-blue-500">→ En moyenne, ça remplace 150€/mois de tableurs, erreurs et temps perdu.</p>
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
							{formatPrice(plan, billingPeriod)}
						</span>
						<span class="text-slate-500 dark:text-slate-400">
							HT{formatPeriod(billingPeriod)}
						</span>
						<div class="mt-1 text-sm text-slate-400 dark:text-slate-500">
							{formatPriceTTC(plan, billingPeriod)}
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
						disabled={checkoutLoading === plan.key}
						onclick={() => openCheckoutModal(plan.key)}
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
						disabled={checkoutLoading === 'lifetime'}
						onclick={() => openCheckoutModal('lifetime')}
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
			Remplace en moyenne 150€/mois de tableurs, erreurs et temps perdu
		</p>

		<div class="mt-8 flex flex-col items-center gap-3">
			<a
				href="/"
				class="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
			>
				<ArrowRight class="h-4 w-4 rotate-180" aria-hidden="true" />
				Retour à l'accueil
			</a>
			{#if isAuthenticated}
				<button
					class="text-sm text-slate-400 underline hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
					onclick={async () => {
						await supabase.auth.signOut();
						window.location.href = '/';
					}}
				>
					Se déconnecter
				</button>
			{/if}
		</div>
	</div>

	<CheckoutConfirmModal
		open={modalOpen}
		planName={modalPlanName}
		planPrice={modalPlanPrice}
		planPeriod={modalPlanPeriod}
		planFeatures={modalPlanFeatures}
		loading={checkoutLoading !== null}
		onConfirm={handleModalConfirm}
		onCancel={() => { modalOpen = false; }}
	/>
</section>
