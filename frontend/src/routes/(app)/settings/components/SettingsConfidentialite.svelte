<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { API_URL } from '$lib/api';
	import { getCurrentSession } from '$lib/auth/session';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { addToast } from '$lib/components/ui/toast';
	import ConfirmDeleteModal from '$lib/components/ConfirmDeleteModal.svelte';

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

	let privacyLoading = $state(false);
	let exportLoading = $state(false);
	let deleteLoading = $state(false);
	let dataSummary = $state<DataSummary | null>(null);
	let showDeleteConfirm = $state(false);
	let deleteConfirmEmail = $state('');
	let privacyLoadError = $state('');

	async function getAccessToken(): Promise<string | null> {
		const session = await getCurrentSession();
		if (!session?.access_token) {
			goto('/login');
			return null;
		}
		return session.access_token;
	}

	async function loadDataSummary() {
		privacyLoading = true;
		privacyLoadError = '';
		try {
			const token = await getAccessToken();
			if (!token) return;

			const response = await fetch(`${API_URL}/api/v1/gdpr/data-summary`, {
				headers: { Authorization: `Bearer ${token}` }
			});

			if (response.ok) {
				dataSummary = await response.json();
			} else {
				privacyLoadError = 'Impossible de charger le résumé des données personnelles.';
			}
		} catch {
			privacyLoadError = 'Erreur réseau pendant le chargement des données personnelles.';
		} finally {
			privacyLoading = false;
		}
	}

	async function exportData() {
		exportLoading = true;
		try {
			const token = await getAccessToken();
			if (!token) return;

			const response = await fetch(`${API_URL}/api/v1/gdpr/data-export`, {
				headers: { Authorization: `Bearer ${token}` }
			});

			if (response.ok) {
				const data = (await response.json()) as { export_url?: string; expires_at?: string };
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
		} catch {
			addToast({ title: 'Erreur réseau', variant: 'error' });
		} finally {
			exportLoading = false;
		}
	}

	async function deleteAccount() {
		deleteLoading = true;
		try {
			const token = await getAccessToken();
			if (!token) return;

			const response = await fetch(`${API_URL}/api/v1/gdpr/account`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});

			if (response.ok) {
				addToast({
					title: 'Compte supprimé avec succès. Redirection...',
					variant: 'success'
				});
				await supabase.auth.signOut();
				setTimeout(() => goto('/'), 2000);
			} else {
				addToast({ title: 'Erreur lors de la suppression du compte', variant: 'error' });
			}
		} catch {
			addToast({ title: 'Erreur réseau', variant: 'error' });
		} finally {
			deleteLoading = false;
			showDeleteConfirm = false;
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

	onMount(() => {
		loadDataSummary();
	});
</script>

<div id="panel-confidentialite" role="tabpanel" aria-labelledby="tab-confidentialite" class="space-y-6">
	{#if privacyLoading}
		<div class="sci-loading" role="status" aria-label="Chargement"></div>
	{:else if !dataSummary}
		<Card class="sci-section-card">
			<CardContent class="py-8">
				<p class="sci-inline-alert sci-inline-alert-error">
					{privacyLoadError || "Impossible de charger les données personnelles. Rechargez la page."}
				</p>
			</CardContent>
		</Card>
	{:else}
		<!-- Data summary -->
		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Résumé des données</CardTitle>
					<CardDescription>Vue d'ensemble des informations stockées sur le compte connecté.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="grid gap-4 pt-0 md:grid-cols-2">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Email</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{dataSummary.email}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Compte créé le</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{formatDate(dataSummary.created_at)}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Dernière connexion</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{formatDateTime(dataSummary.data_summary.last_sign_in)}</p>
				</div>
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Données stockées</p>
					<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
						{dataSummary.data_summary.sci_count} SCI ·
						{dataSummary.data_summary.biens_count} biens ·
						{dataSummary.data_summary.loyers_count} loyers ·
						{dataSummary.data_summary.associes_count} associés
					</p>
				</div>
			</CardContent>
		</Card>

		<!-- Export -->
		<Card class="sci-section-card">
			<CardHeader>
				<div>
					<CardTitle class="text-lg">Export des données (JSON)</CardTitle>
					<CardDescription>Droit à la portabilité (RGPD Art. 20). Téléchargez une copie complète de vos données.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="space-y-4 pt-0">
				<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
					<p class="text-sm text-slate-700 dark:text-slate-300">
						L'export contient toutes les données rattachées au compte dans un fichier JSON structuré :
					</p>
					<ul class="mt-2 list-inside list-disc space-y-1 text-sm text-slate-600 dark:text-slate-400">
						<li>Informations du compte (email, dates de création et connexion)</li>
						<li>SCI et associés</li>
						<li>Biens immobiliers</li>
						<li>Loyers enregistrés</li>
						<li>Charges et données fiscales</li>
					</ul>
					<p class="mt-3 text-xs text-slate-500 dark:text-slate-500">
						Le lien de téléchargement est valide 30 minutes. L'export est limité à 3 demandes par heure.
					</p>
				</div>

				<Button onclick={exportData} disabled={exportLoading} class="w-full sm:w-auto">
					{#if exportLoading}
						<span class="flex items-center gap-2">
							<svg class="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
							</svg>
							Export en cours...
						</span>
					{:else}
						Télécharger mes données (JSON)
					{/if}
				</Button>
			</CardContent>
		</Card>

		<!-- Delete account -->
		<Card class="sci-section-card border-red-200 dark:border-red-900">
			<CardHeader>
				<div>
					<CardTitle class="text-red-600 dark:text-red-400">Suppression du compte</CardTitle>
					<CardDescription>Droit à l'effacement (RGPD Art. 17). Cette action est définitive et irréversible.</CardDescription>
				</div>
			</CardHeader>
			<CardContent class="space-y-4 pt-0">
				<div class="rounded-2xl bg-red-50 p-4 dark:bg-red-900/20">
					<p class="mb-2 text-sm font-semibold text-red-800 dark:text-red-300">
						Attention : action irréversible
					</p>
					<p class="text-sm text-red-700 dark:text-red-400">
						La suppression du compte entraîne l'effacement définitif de :
					</p>
					<ul class="mt-2 list-inside list-disc space-y-1 text-sm text-red-700 dark:text-red-400">
						<li>Toutes les SCI ({dataSummary.data_summary.sci_count}) et leurs associés ({dataSummary.data_summary.associes_count})</li>
						<li>Tous les biens immobiliers ({dataSummary.data_summary.biens_count})</li>
						<li>Tous les loyers ({dataSummary.data_summary.loyers_count}), charges et données fiscales</li>
						<li>Tous les documents uploadés</li>
					</ul>
					<p class="mt-3 text-xs text-red-600 dark:text-red-500">
						Les données de facturation Stripe sont anonymisées (non supprimées) pour respecter les obligations légales de conservation de 10 ans (Code Général des Impôts).
					</p>
				</div>

				<Button variant="destructive" onclick={() => (showDeleteConfirm = true)}>
					Supprimer définitivement mon compte
				</Button>

				<ConfirmDeleteModal
					open={showDeleteConfirm}
					entityName={dataSummary.email}
					entityType="votre compte"
					warningMessage="La suppression du compte entraîne l'effacement définitif de toutes vos SCI ({dataSummary.data_summary.sci_count}), biens ({dataSummary.data_summary.biens_count}), loyers ({dataSummary.data_summary.loyers_count}), associés ({dataSummary.data_summary.associes_count}) et documents. Les données de facturation Stripe sont anonymisées. Cette action est irréversible."
					loading={deleteLoading}
					onConfirm={deleteAccount}
					onCancel={() => { showDeleteConfirm = false; deleteConfirmEmail = ''; }}
				/>
			</CardContent>
		</Card>

		<!-- RGPD contact -->
		<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
			<div class="flex flex-wrap gap-6">
				<div>
					<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Contact RGPD</p>
					<a href="mailto:privacy@gerersci.fr" class="mt-1 text-cyan-600 underline-offset-4 hover:underline dark:text-cyan-300">
						privacy@gerersci.fr
					</a>
				</div>
				<div>
					<p class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Autorité de contrôle</p>
					<a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer" class="mt-1 text-cyan-600 underline-offset-4 hover:underline dark:text-cyan-300">
						CNIL
					</a>
				</div>
			</div>
		</div>
	{/if}
</div>
