<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchSubscriptionEntitlements, type SubscriptionEntitlements } from '$lib/api';
	import WorkspaceActionBar from '$lib/components/WorkspaceActionBar.svelte';
	import WorkspaceHeader from '$lib/components/WorkspaceHeader.svelte';
	import WorkspaceRailCard from '$lib/components/WorkspaceRailCard.svelte';
	import { addToast } from '$lib/components/ui/toast';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { formatApiErrorMessage } from '$lib/high-value/presentation';
	import {
		DEFAULT_APPLICATION_PREFERENCES,
		readApplicationPreferences,
		saveApplicationPreferences,
		type ApplicationLandingRoute,
		type ApplicationPreferences
	} from '$lib/settings/application-preferences';

	const landingRouteOptions: Array<{ value: ApplicationLandingRoute; label: string }> = [
		{ value: '/dashboard', label: 'Cockpit' },
		{ value: '/scis', label: 'Portefeuille' },
		{ value: '/exploitation', label: 'Exploitation' },
		{ value: '/finance', label: 'Finance' },
		{ value: '/settings', label: "Paramètres de l'application" }
	];

	let preferences: ApplicationPreferences = { ...DEFAULT_APPLICATION_PREFERENCES };
	let subscription: SubscriptionEntitlements | null = null;
	let subscriptionError = '';

	$: landingRouteLabel =
		landingRouteOptions.find((option) => option.value === preferences.defaultLandingRoute)?.label ??
		'Cockpit';
	$: densityLabel = preferences.density === 'compact' ? 'Compacte' : 'Confortable';

	onMount(async () => {
		preferences = readApplicationPreferences();
		try {
			subscription = await fetchSubscriptionEntitlements();
		} catch (error) {
			subscriptionError = formatApiErrorMessage(error, "Impossible de charger l'offre active.");
		}
	});

	function handleSave() {
		saveApplicationPreferences(preferences);
		addToast({
			title: 'Paramètres enregistrés',
			description: "Les préférences d'application ont été mises à jour sur ce navigateur.",
			variant: 'success'
		});
	}
</script>

<svelte:head>
	<title>Paramètres — GererSCI</title>
	<meta name="description" content="Préférences d'interface et configuration." />
</svelte:head>

<section class="sci-page-shell">
	<WorkspaceHeader
		eyebrow="Paramètres • expérience opérateur"
		title="Préférences de l'application"
		subtitle="Les paramètres pilotent uniquement l’expérience locale du navigateur: point d’entrée, densité, PDF et signaux. L’identité et l’offre restent dans Compte."
		contextLabel="Configuration active"
		contextValue={`${landingRouteLabel} • ${densityLabel}`}
		contextDetail={preferences.showPdfPreview
			? 'Prévisualisation PDF active.'
			: 'Prévisualisation PDF désactivée.'}
	>
		<Button href="/account">Ouvrir le compte</Button>
		<Button href="/dashboard" variant="outline">Retour au cockpit</Button>
	</WorkspaceHeader>

	<WorkspaceActionBar
		eyebrow="Cadre des préférences"
		title="Réglages locaux, pas décisions métier"
		description="On ajuste ici la façon dont l’espace de pilotage s’ouvre et se lit sur ce navigateur. Les paramètres ne doivent pas concurrencer les écrans métier."
	>
		<div class="sci-action-grid">
			<div class="sci-action-card">
				<p class="sci-action-card-title">Point d’entrée</p>
				<p class="sci-action-card-value">{landingRouteLabel}</p>
				<p class="sci-action-card-body">Page ouverte après connexion sur ce navigateur.</p>
			</div>
			<div class="sci-action-card">
				<p class="sci-action-card-title">Densité</p>
				<p class="sci-action-card-value">{densityLabel}</p>
				<p class="sci-action-card-body">
					Réglage de lecture appliqué à l’ensemble du shell connecté.
				</p>
			</div>
			<div class="sci-action-card">
				<p class="sci-action-card-title">Signaux</p>
				<p class="sci-action-card-value">
					{preferences.riskAlertsEnabled ? 'Alertes actives' : 'Alertes neutres'}
				</p>
				<p class="sci-action-card-body">
					Met en avant ou non les retards et risques dans les vues clés.
				</p>
			</div>
		</div>
		<div class="sci-primary-actions mt-5">
			<Button onclick={handleSave}>Enregistrer les paramètres</Button>
			<Button href="/account" variant="outline">Revenir au compte</Button>
		</div>
		{#snippet aside()}
			<WorkspaceRailCard
				title="Lecture immédiate"
				description="Le panneau de droite rappelle les réglages actifs et l’impact de l’offre sans mélanger les actions du compte."
			>
				<div class="space-y-3">
					<div class="sci-action-card">
						<p class="sci-action-card-title">PDF</p>
						<p class="sci-action-card-value">
							{preferences.showPdfPreview ? 'Preview active' : 'Download prioritaire'}
						</p>
					</div>
					{#if subscription}
						<div class="sci-action-card">
							<p class="sci-action-card-title">Capacité active</p>
							<p class="sci-action-card-value">{subscription.plan_name}</p>
							<p class="sci-action-card-body">
								{subscription.max_scis == null
									? 'SCI illimitées'
									: `${subscription.remaining_scis ?? 0} SCI restantes`}
								•
								{subscription.max_biens == null
									? 'Biens illimités'
									: `${subscription.remaining_biens ?? 0} biens restants`}
							</p>
						</div>
					{/if}
				</div>
			</WorkspaceRailCard>
		{/snippet}
	</WorkspaceActionBar>

	<div class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Préférences d'expérience</CardTitle>
					<CardDescription
						>Ces réglages sont propres au navigateur courant et s’appliquent à tout l’espace
						connecté.</CardDescription
					>
				</div>
			</CardHeader>
			<CardContent class="space-y-6 pt-0">
				<label class="sci-field" for="settings-landing-route">
					<span class="sci-field-label">Page d'ouverture par défaut</span>
					<select
						id="settings-landing-route"
						name="settings-landing-route"
						class="sci-select"
						bind:value={preferences.defaultLandingRoute}
					>
						{#each landingRouteOptions as option (option.value)}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</label>

				<label class="sci-field" for="settings-density">
					<span class="sci-field-label">Densité d'affichage</span>
					<select
						id="settings-density"
						name="settings-density"
						class="sci-select"
						bind:value={preferences.density}
					>
						<option value="comfortable">Confortable</option>
						<option value="compact">Compacte</option>
					</select>
				</label>

				<div class="grid gap-3 md:grid-cols-3">
					<label class="rounded-2xl border border-border bg-muted p-4 text-sm">
						<div class="flex items-start justify-between gap-3">
							<div>
								<p class="font-semibold text-foreground">Prévisualisation PDF</p>
								<p class="mt-1 text-muted-foreground">
									Affiche les quittances directement dans l’interface.
								</p>
							</div>
							<input
								type="checkbox"
								bind:checked={preferences.showPdfPreview}
								aria-label="Activer la prévisualisation PDF"
							/>
						</div>
					</label>

					<label class="rounded-2xl border border-border bg-muted p-4 text-sm">
						<div class="flex items-start justify-between gap-3">
							<div>
								<p class="font-semibold text-foreground">Digest email</p>
								<p class="mt-1 text-muted-foreground">
									Préférence de réception des rappels et synthèses.
								</p>
							</div>
							<input
								type="checkbox"
								bind:checked={preferences.emailDigestEnabled}
								aria-label="Activer le digest email"
							/>
						</div>
					</label>

					<label class="rounded-2xl border border-border bg-muted p-4 text-sm">
						<div class="flex items-start justify-between gap-3">
							<div>
								<p class="font-semibold text-foreground">Alertes de risque</p>
								<p class="mt-1 text-muted-foreground">
									Priorise les retards et charges anormales dans les vues clés.
								</p>
							</div>
							<input
								type="checkbox"
								bind:checked={preferences.riskAlertsEnabled}
								aria-label="Activer les alertes de risque"
							/>
						</div>
					</label>
				</div>
			</CardContent>
		</Card>

		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Impact des réglages</CardTitle>
					<CardDescription
						>Lecture immédiate de la configuration active sur ce navigateur, sans mélanger cela avec
						les actions de compte.</CardDescription
					>
				</div>
			</CardHeader>
			<CardContent class="grid gap-3 pt-0">
				<div class="rounded-2xl border border-border bg-muted p-4 text-sm">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-muted-foreground uppercase">
						Point d’entrée
					</p>
					<p class="mt-2 text-base font-semibold text-foreground">{landingRouteLabel}</p>
					<p class="mt-1 text-muted-foreground">
						La première page ouverte après connexion sur ce navigateur.
					</p>
				</div>
				<div class="rounded-2xl border border-border bg-muted p-4 text-sm">
					<p class="text-[0.68rem] font-semibold tracking-[0.18em] text-muted-foreground uppercase">
						Densité d’affichage
					</p>
					<p class="mt-2 text-base font-semibold text-foreground">{densityLabel}</p>
					<p class="mt-1 text-muted-foreground">
						{preferences.density === 'compact'
							? 'Priorise la densité d’information pour les revues opérateur.'
							: 'Laisse davantage d’air entre les blocs pour un pilotage confortable.'}
					</p>
				</div>
				<div class="grid gap-3 md:grid-cols-2">
					<div class="rounded-2xl border border-border bg-card p-4 text-sm">
						<p class="font-semibold text-foreground">PDF</p>
						<p class="mt-1 text-muted-foreground">
							{preferences.showPdfPreview
								? 'Prévisualisation intégrée active.'
								: 'Téléchargement sans preview priorisé.'}
						</p>
					</div>
					<div class="rounded-2xl border border-border bg-card p-4 text-sm">
						<p class="font-semibold text-foreground">Alertes</p>
						<p class="mt-1 text-muted-foreground">
							{preferences.riskAlertsEnabled
								? 'Les signaux de risque sont mis en avant.'
								: 'Les vues restent neutres sans priorisation des risques.'}
						</p>
					</div>
				</div>
				{#if subscription}
					<div class="rounded-2xl border border-border bg-muted p-4 text-sm">
						<p
							class="text-[0.68rem] font-semibold tracking-[0.18em] text-muted-foreground uppercase"
						>
							Capacité active
						</p>
						<p class="mt-2 text-base font-semibold text-foreground">{subscription.plan_name}</p>
						<p class="mt-1 text-muted-foreground">
							{subscription.max_scis == null
								? 'SCI illimitées'
								: `${subscription.remaining_scis ?? 0} SCI restantes`}
							•
							{subscription.max_biens == null
								? 'Biens illimités'
								: `${subscription.remaining_biens ?? 0} biens restants`}
						</p>
					</div>
				{:else if subscriptionError}
					<p class="sci-inline-alert sci-inline-alert-error">{subscriptionError}</p>
				{/if}
				<div class="grid gap-2 border-t border-border pt-3">
					<Button href="/account" variant="outline" class="justify-start">Aller au compte</Button>
					<Button href="/account/privacy" variant="outline" class="justify-start"
						>Ouvrir la confidentialité</Button
					>
				</div>
			</CardContent>
		</Card>
	</div>
</section>
