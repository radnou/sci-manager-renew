<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import EmptyStateOperator from '$lib/components/EmptyStateOperator.svelte';
	import PageSpecificSkeleton from '$lib/components/PageSpecificSkeleton.svelte';
	import WorkspaceActionBar from '$lib/components/WorkspaceActionBar.svelte';
	import WorkspaceHeader from '$lib/components/WorkspaceHeader.svelte';
	import WorkspaceRailCard from '$lib/components/WorkspaceRailCard.svelte';
	import { getCurrentSession } from '$lib/auth/session';
	import { supabase } from '$lib/supabase';
	import { API_URL } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import {
		Card,
		CardContent,
		CardDescription,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { addToast } from '$lib/components/ui/toast';

	interface DataSummary {
		user_id: string;
		email: string;
		created_at: string;
		data_summary: {
			sci_count: number;
			biens_count: number;
			loyers_count: number;
			associes_count: number;
			account_created: string;
			last_sign_in: string;
		};
	}

	let loading = $state(false);
	let exportLoading = $state(false);
	let deleteLoading = $state(false);
	let dataSummary = $state<DataSummary | null>(null);
	let showDeleteConfirm = $state(false);
	let deleteConfirmEmail = $state('');
	let loadError = $state('');

	onMount(async () => {
		await loadDataSummary();
	});

	async function getAccessToken(): Promise<string | null> {
		const session = await getCurrentSession();
		if (!session?.access_token) {
			goto('/login');
			return null;
		}
		return session.access_token;
	}

	async function loadDataSummary() {
		loading = true;
		loadError = '';
		try {
			const token = await getAccessToken();
			if (!token) return;

			const response = await fetch(`${API_URL}/api/v1/gdpr/data-summary`, {
				headers: {
					Authorization: `Bearer ${token}`
				}
			});

			if (response.ok) {
				dataSummary = await response.json();
			} else {
				loadError = 'Impossible de charger le resume des donnees personnelles.';
				addToast({
					title: 'Erreur lors du chargement du resume des donnees',
					variant: 'error'
				});
			}
		} catch (error) {
			loadError = 'Erreur reseau pendant le chargement des donnees personnelles.';
			addToast({ title: 'Erreur reseau', variant: 'error' });
			console.error(error);
		} finally {
			loading = false;
		}
	}

	async function exportData() {
		exportLoading = true;
		try {
			const token = await getAccessToken();
			if (!token) return;

			const response = await fetch(`${API_URL}/api/v1/gdpr/data-export`, {
				headers: {
					Authorization: `Bearer ${token}`
				}
			});

			if (response.ok) {
				const data = (await response.json()) as {
					export_url?: string;
					expires_at?: string;
				};
				if (data.export_url) {
					window.open(data.export_url, '_blank', 'noopener,noreferrer');
					addToast({
						title: 'Export prêt. Le téléchargement a été ouvert dans un nouvel onglet.',
						variant: 'success'
					});
				} else {
					addToast({
						title: "Export créé, mais aucun lien de téléchargement n'a été retourné.",
						variant: 'error'
					});
				}
			} else {
				addToast({ title: "Erreur lors de l'export des données", variant: 'error' });
			}
		} catch (error) {
			addToast({ title: 'Erreur reseau', variant: 'error' });
			console.error(error);
		} finally {
			exportLoading = false;
		}
	}

	function isDeleteConfirmValid(): boolean {
		if (!dataSummary?.email) return false;
		return deleteConfirmEmail.trim().toLowerCase() === dataSummary.email.trim().toLowerCase();
	}

	async function deleteAccount() {
		if (!isDeleteConfirmValid()) {
			addToast({
				title: 'Veuillez saisir votre adresse email pour confirmer la suppression',
				variant: 'error'
			});
			return;
		}

		deleteLoading = true;
		try {
			const token = await getAccessToken();
			if (!token) return;

			const response = await fetch(`${API_URL}/api/v1/gdpr/account`, {
				method: 'DELETE',
				headers: {
					Authorization: `Bearer ${token}`
				}
			});

			if (response.ok) {
				addToast({
					title: 'Compte supprime avec succes. Redirection...',
					variant: 'success'
				});
				await supabase.auth.signOut();
				setTimeout(() => goto('/'), 2000);
			} else {
				addToast({
					title: 'Erreur lors de la suppression du compte',
					variant: 'error'
				});
			}
		} catch (error) {
			addToast({ title: 'Erreur reseau', variant: 'error' });
			console.error(error);
		} finally {
			deleteLoading = false;
		}
	}

	function formatDate(dateStr: string | null | undefined): string {
		if (!dateStr || dateStr === 'None') return 'Non disponible';
		try {
			return new Date(dateStr).toLocaleDateString('fr-FR', {
				day: 'numeric',
				month: 'long',
				year: 'numeric'
			});
		} catch {
			return 'Non disponible';
		}
	}

	function formatDateTime(dateStr: string | null | undefined): string {
		if (!dateStr || dateStr === 'None') return 'Non disponible';
		try {
			return new Date(dateStr).toLocaleDateString('fr-FR', {
				day: 'numeric',
				month: 'long',
				year: 'numeric',
				hour: '2-digit',
				minute: '2-digit'
			});
		} catch {
			return 'Non disponible';
		}
	}
</script>

<svelte:head>
	<title>Mes Donnees Personnelles - GererSCI</title>
</svelte:head>

<section class="sci-page-shell">
	<WorkspaceHeader
		eyebrow="Confidentialite - droits RGPD"
		title="Donnees et confidentialite"
		subtitle="Export, transparence et suppression du compte. Les demandes RGPD sont centralisees ici, separees des preferences locales."
		contextLabel="Compte concerne"
		contextValue={dataSummary?.email || 'Session connectee'}
		contextDetail={dataSummary
			? `${dataSummary.data_summary.sci_count} SCI - ${dataSummary.data_summary.biens_count} biens - ${dataSummary.data_summary.loyers_count} loyers`
			: 'Les demandes RGPD portent sur toutes les donnees rattachees au compte.'}
	>
		<Button onclick={exportData} disabled={exportLoading}>
			{exportLoading ? 'Export en cours...' : 'Exporter mes donnees'}
		</Button>
		<Button href="/account" variant="outline">Retour au compte</Button>
	</WorkspaceHeader>

	{#if loading}
		<PageSpecificSkeleton
			mode="hub"
			eyebrow="Chargement confidentialite"
			title="Preparation des donnees personnelles"
			description="Consolidation du resume du compte, des volumes stockes et des actions RGPD disponibles."
		/>
	{:else if !dataSummary}
		<EmptyStateOperator
			eyebrow="Resume indisponible"
			title="Impossible de charger les donnees personnelles"
			description={loadError ||
				"Le resume RGPD n'a pas pu etre recupere. Revenez au compte ou rechargez la page."}
			primaryHref="/account"
			primaryLabel="Retour au compte"
			secondaryHref="/dashboard"
			secondaryLabel="Retour au tableau de bord"
		/>
	{:else}
		<WorkspaceActionBar
			eyebrow="Cadre RGPD"
			title="Transparence, portabilite, suppression"
			description="Le perimetre stocke est affiche en lecture seule. L'export genere un fichier JSON complet. La suppression du compte est irreversible et necessite une confirmation explicite."
		>
			<div class="sci-action-grid">
				<div class="sci-action-card">
					<p class="sci-action-card-title">Perimetre stocke</p>
					<p class="sci-action-card-value">
						{dataSummary.data_summary.sci_count} SCI - {dataSummary.data_summary
							.biens_count} biens
					</p>
					<p class="sci-action-card-body">
						Resume des donnees principales rattachees au compte.
					</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Portabilite</p>
					<p class="sci-action-card-value">Export JSON complet</p>
					<p class="sci-action-card-body">
						Telecharge une copie structuree de toutes les donnees personnelles et metier.
					</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Suppression</p>
					<p class="sci-action-card-value">Confirmation par email requise</p>
					<p class="sci-action-card-body">
						La suppression du compte est irreversible et necessite la saisie de l'adresse
						email.
					</p>
				</div>
			</div>
			<div class="mt-5 sci-primary-actions">
				<Button onclick={exportData} disabled={exportLoading}>
					{exportLoading ? 'Export en cours...' : 'Exporter mes donnees'}
				</Button>
				<Button href="/account" variant="outline">Ouvrir le compte</Button>
				<Button href="/dashboard" variant="outline">Retour au tableau de bord</Button>
			</div>
			{#snippet aside()}
				<WorkspaceRailCard
					title="Support et recours"
					description="Canal RGPD direct et recours externe si les droits ne sont pas respectes."
				>
					<div class="space-y-3 text-sm text-slate-500 dark:text-slate-400">
						<div class="sci-action-card">
							<p class="sci-action-card-title">Contact RGPD</p>
							<p class="sci-action-card-value">
								<a
									href="mailto:privacy@gerersci.fr"
									class="text-cyan-600 underline-offset-4 hover:underline dark:text-cyan-300"
								>
									privacy@gerersci.fr
								</a>
							</p>
						</div>
						<div class="sci-action-card">
							<p class="sci-action-card-title">Autorite de controle</p>
							<p class="sci-action-card-value">
								<a
									href="https://www.cnil.fr"
									target="_blank"
									rel="noopener noreferrer"
									class="text-cyan-600 underline-offset-4 hover:underline dark:text-cyan-300"
								>
									CNIL
								</a>
							</p>
						</div>
					</div>
				</WorkspaceRailCard>
			{/snippet}
		</WorkspaceActionBar>

		<!-- Section 1: Resume des donnees -->
		<div class="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle>Resume des donnees</CardTitle>
					<CardDescription
						>Vue d'ensemble des informations stockees sur le compte connecte.</CardDescription
					>
				</CardHeader>
				<CardContent class="grid gap-4 pt-0 md:grid-cols-2">
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p
							class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500"
						>
							Email
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{dataSummary.email}
						</p>
					</div>
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p
							class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500"
						>
							Compte cree le
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{formatDate(dataSummary.created_at)}
						</p>
					</div>
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p
							class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500"
						>
							Derniere connexion
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{formatDateTime(dataSummary.data_summary.last_sign_in)}
						</p>
					</div>
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p
							class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500"
						>
							Nombre de SCI
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{dataSummary.data_summary.sci_count}
						</p>
					</div>
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p
							class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500"
						>
							Nombre de biens
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{dataSummary.data_summary.biens_count}
						</p>
					</div>
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p
							class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500"
						>
							Nombre de loyers
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{dataSummary.data_summary.loyers_count}
						</p>
					</div>
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p
							class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500"
						>
							Nombre d'associes
						</p>
						<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
							{dataSummary.data_summary.associes_count}
						</p>
					</div>
				</CardContent>
			</Card>

			<!-- Section 2: Export des donnees -->
			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle>Export des donnees (JSON)</CardTitle>
					<CardDescription
						>Droit a la portabilite (RGPD Art. 20). Telechargez une copie complete de
						vos donnees.</CardDescription
					>
				</CardHeader>
				<CardContent class="space-y-4 pt-0">
					<div
						class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
					>
						<p class="text-sm text-slate-700 dark:text-slate-300">
							L'export contient toutes les donnees rattachees au compte dans un fichier
							JSON structure :
						</p>
						<ul
							class="mt-2 list-inside list-disc space-y-1 text-sm text-slate-600 dark:text-slate-400"
						>
							<li>Informations du compte (email, dates de creation et connexion)</li>
							<li>SCI et associes</li>
							<li>Biens immobiliers</li>
							<li>Loyers enregistrés</li>
							<li>Charges et données fiscales</li>
						</ul>
						<p class="mt-3 text-xs text-slate-500 dark:text-slate-500">
							Le lien de téléchargement est valide 30 minutes. L'export est limité à 3
							demandes par heure.
						</p>
					</div>

					<Button onclick={exportData} disabled={exportLoading} class="w-full sm:w-auto">
						{#if exportLoading}
							<span class="flex items-center gap-2">
								<svg
									class="h-4 w-4 animate-spin"
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
								>
									<circle
										class="opacity-25"
										cx="12"
										cy="12"
										r="10"
										stroke="currentColor"
										stroke-width="4"
									></circle>
									<path
										class="opacity-75"
										fill="currentColor"
										d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
									></path>
								</svg>
								Export en cours...
							</span>
						{:else}
							Telecharger mes donnees (JSON)
						{/if}
					</Button>
				</CardContent>
			</Card>
		</div>

		<!-- Section 3: Suppression du compte -->
		<Card class="sci-section-card mt-6 border-red-200 dark:border-red-900">
			<CardHeader>
				<CardTitle class="text-red-600 dark:text-red-400">Suppression du compte</CardTitle>
				<CardDescription
					>Droit a l'effacement (RGPD Art. 17). Cette action est definitive et
					irreversible.</CardDescription
				>
			</CardHeader>
			<CardContent class="space-y-4 pt-0">
				<div class="rounded-2xl bg-red-50 p-4 dark:bg-red-900/20">
					<p class="mb-2 text-sm font-semibold text-red-800 dark:text-red-300">
						Attention : action irreversible
					</p>
					<p class="text-sm text-red-700 dark:text-red-400">
						La suppression du compte entraine l'effacement definitif de :
					</p>
					<ul
						class="mt-2 list-inside list-disc space-y-1 text-sm text-red-700 dark:text-red-400"
					>
						<li>
							Toutes les SCI ({dataSummary.data_summary.sci_count}) et leurs associes ({dataSummary
								.data_summary.associes_count})
						</li>
						<li>
							Tous les biens immobiliers ({dataSummary.data_summary.biens_count})
						</li>
						<li>
							Tous les loyers ({dataSummary.data_summary.loyers_count}), charges et
							donnees fiscales
						</li>
						<li>Tous les documents uploades</li>
					</ul>
					<p class="mt-3 text-xs text-red-600 dark:text-red-500">
						Les donnees de facturation Stripe sont anonymisees (non supprimees) pour
						respecter les obligations legales de conservation de 10 ans (Code General des
						Impots).
					</p>
				</div>

				{#if !showDeleteConfirm}
					<Button variant="destructive" onclick={() => (showDeleteConfirm = true)}>
						Supprimer definitivement mon compte
					</Button>
				{:else}
					<div
						class="space-y-4 rounded-2xl border border-red-300 bg-red-50/50 p-4 dark:border-red-800 dark:bg-red-950/30"
					>
						<p class="text-sm font-semibold text-red-800 dark:text-red-300">
							Pour confirmer la suppression, saisissez votre adresse email :
						</p>
						<p class="font-mono text-sm text-red-600 dark:text-red-400">
							{dataSummary.email}
						</p>

						<div>
							<input
								type="email"
								bind:value={deleteConfirmEmail}
								placeholder={dataSummary.email}
								autocomplete="off"
								spellcheck="false"
								class="w-full max-w-md rounded-lg border border-red-300 bg-white px-3 py-2 text-sm focus:border-red-500 focus:ring-2 focus:ring-red-200 focus:outline-none dark:border-red-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:ring-red-800"
							/>
							{#if deleteConfirmEmail && !isDeleteConfirmValid()}
								<p class="mt-1 text-xs text-red-500">
									L'adresse email ne correspond pas.
								</p>
							{/if}
						</div>

						<div class="flex flex-wrap gap-2">
							<Button
								variant="destructive"
								onclick={deleteAccount}
								disabled={deleteLoading || !isDeleteConfirmValid()}
							>
								{#if deleteLoading}
									<span class="flex items-center gap-2">
										<svg
											class="h-4 w-4 animate-spin"
											xmlns="http://www.w3.org/2000/svg"
											fill="none"
											viewBox="0 0 24 24"
										>
											<circle
												class="opacity-25"
												cx="12"
												cy="12"
												r="10"
												stroke="currentColor"
												stroke-width="4"
											></circle>
											<path
												class="opacity-75"
												fill="currentColor"
												d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
											></path>
										</svg>
										Suppression en cours...
									</span>
								{:else}
									Confirmer la suppression definitive
								{/if}
							</Button>
							<Button
								variant="outline"
								onclick={() => {
									showDeleteConfirm = false;
									deleteConfirmEmail = '';
								}}
							>
								Annuler
							</Button>
						</div>
					</div>
				{/if}
			</CardContent>
		</Card>
	{/if}
</section>
