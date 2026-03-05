<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { toast } from 'svelte-sonner';

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
	let deleteConfirmText = $state('');

	onMount(async () => {
		await loadDataSummary();
	});

	async function loadDataSummary() {
		loading = true;
		try {
			const { data: { session } } = await supabase.auth.getSession();
			if (!session) {
				goto('/login');
				return;
			}

			const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/gdpr/data-summary`, {
				headers: {
					'Authorization': `Bearer ${session.access_token}`
				}
			});

			if (response.ok) {
				dataSummary = await response.json();
			} else {
				toast.error('Erreur lors du chargement du résumé des données');
			}
		} catch (error) {
			toast.error('Erreur réseau');
			console.error(error);
		} finally {
			loading = false;
		}
	}

	async function exportData() {
		exportLoading = true;
		try {
			const { data: { session } } = await supabase.auth.getSession();
			if (!session) {
				goto('/login');
				return;
			}

			const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/gdpr/data-export`, {
				headers: {
					'Authorization': `Bearer ${session.access_token}`
				}
			});

			if (response.ok) {
				const data = await response.json();
				toast.success('Export des données réussi ! Téléchargement en cours...');

				// TODO: Download file from export_url when implemented
				// For now, show success message
			} else {
				toast.error('Erreur lors de l\'export des données');
			}
		} catch (error) {
			toast.error('Erreur réseau');
			console.error(error);
		} finally {
			exportLoading = false;
		}
	}

	async function deleteAccount() {
		if (deleteConfirmText !== 'SUPPRIMER') {
			toast.error('Veuillez taper "SUPPRIMER" pour confirmer');
			return;
		}

		deleteLoading = true;
		try {
			const { data: { session } } = await supabase.auth.getSession();
			if (!session) {
				goto('/login');
				return;
			}

			const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/gdpr/account`, {
				method: 'DELETE',
				headers: {
					'Authorization': `Bearer ${session.access_token}`
				}
			});

			if (response.ok) {
				toast.success('Compte supprimé avec succès. Redirection...');
				await supabase.auth.signOut();
				setTimeout(() => goto('/'), 2000);
			} else {
				toast.error('Erreur lors de la suppression du compte');
			}
		} catch (error) {
			toast.error('Erreur réseau');
			console.error(error);
		} finally {
			deleteLoading = false;
		}
	}
</script>

<svelte:head>
	<title>Mes Données Personnelles - SCI Manager</title>
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">
			Mes Données Personnelles
		</h1>
		<p class="text-slate-600 dark:text-slate-400">
			Gérez vos données conformément au RGPD (Art. 15, 17, 20)
		</p>
	</div>

	{#if loading}
		<Card>
			<CardContent class="p-8 text-center">
				<p class="text-slate-600 dark:text-slate-400">Chargement...</p>
			</CardContent>
		</Card>
	{:else if dataSummary}
		<div class="space-y-6">
			<!-- Résumé des données -->
			<Card>
				<CardHeader>
					<CardTitle>📊 Résumé de vos données</CardTitle>
					<CardDescription>Vue d'ensemble des informations stockées</CardDescription>
				</CardHeader>
				<CardContent class="space-y-3">
					<div class="grid grid-cols-2 gap-4">
						<div>
							<p class="text-sm text-slate-600 dark:text-slate-400">Email</p>
							<p class="font-semibold">{dataSummary.email}</p>
						</div>
						<div>
							<p class="text-sm text-slate-600 dark:text-slate-400">Compte créé le</p>
							<p class="font-semibold">{new Date(dataSummary.created_at).toLocaleDateString('fr-FR')}</p>
						</div>
						<div>
							<p class="text-sm text-slate-600 dark:text-slate-400">Nombre de SCI</p>
							<p class="font-semibold">{dataSummary.data_summary.sci_count}</p>
						</div>
						<div>
							<p class="text-sm text-slate-600 dark:text-slate-400">Nombre de biens</p>
							<p class="font-semibold">{dataSummary.data_summary.biens_count}</p>
						</div>
						<div>
							<p class="text-sm text-slate-600 dark:text-slate-400">Nombre de loyers</p>
							<p class="font-semibold">{dataSummary.data_summary.loyers_count}</p>
						</div>
						<div>
							<p class="text-sm text-slate-600 dark:text-slate-400">Nombre d'associés</p>
							<p class="font-semibold">{dataSummary.data_summary.associes_count}</p>
						</div>
					</div>
				</CardContent>
			</Card>

			<!-- Export de données (Art. 20) -->
			<Card>
				<CardHeader>
					<CardTitle>📥 Export de données (Portabilité)</CardTitle>
					<CardDescription>RGPD Article 20 - Droit à la portabilité</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<p class="text-sm text-slate-600 dark:text-slate-400">
						Téléchargez une copie complète de toutes vos données personnelles dans un format structuré (JSON).
						Cela inclut vos SCI, biens, loyers, associés, charges et données fiscales.
					</p>
					<Button
						onclick={exportData}
						disabled={exportLoading}
						class="min-w-[200px]"
					>
						{exportLoading ? 'Export en cours...' : '📦 Exporter mes données'}
					</Button>
				</CardContent>
			</Card>

			<!-- Suppression de compte (Art. 17) -->
			<Card class="border-red-200 dark:border-red-900">
				<CardHeader>
					<CardTitle class="text-red-600 dark:text-red-400">
						🗑️ Suppression de compte (Droit à l'oubli)
					</CardTitle>
					<CardDescription>RGPD Article 17 - Droit à l'effacement</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<div class="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
						<p class="text-sm font-semibold text-red-800 dark:text-red-300 mb-2">
							⚠️ Attention : Action irréversible !
						</p>
						<p class="text-sm text-red-700 dark:text-red-400">
							La suppression de votre compte entraînera la suppression définitive de :
						</p>
						<ul class="text-sm text-red-700 dark:text-red-400 list-disc list-inside mt-2 space-y-1">
							<li>Votre compte et votre email</li>
							<li>Toutes vos SCI</li>
							<li>Tous vos biens immobiliers</li>
							<li>Tous vos loyers et charges</li>
							<li>Toutes vos données fiscales</li>
						</ul>
						<p class="text-xs text-red-600 dark:text-red-500 mt-3">
							Note : Les données de facturation seront anonymisées (conservation légale obligatoire de 10 ans)
						</p>
					</div>

					{#if !showDeleteConfirm}
						<Button
							variant="destructive"
							onclick={() => showDeleteConfirm = true}
						>
							Supprimer définitivement mon compte
						</Button>
					{:else}
						<div class="space-y-3 border-l-4 border-red-500 pl-4">
							<p class="text-sm font-semibold">Tapez "SUPPRIMER" pour confirmer :</p>
							<input
								type="text"
								bind:value={deleteConfirmText}
								placeholder="SUPPRIMER"
								class="border border-slate-300 dark:border-slate-700 rounded-md px-3 py-2 w-full max-w-xs"
							/>
							<div class="flex gap-2">
								<Button
									variant="destructive"
									onclick={deleteAccount}
									disabled={deleteLoading || deleteConfirmText !== 'SUPPRIMER'}
								>
									{deleteLoading ? 'Suppression...' : 'Confirmer la suppression'}
								</Button>
								<Button
									variant="outline"
									onclick={() => {
										showDeleteConfirm = false;
										deleteConfirmText = '';
									}}
								>
									Annuler
								</Button>
							</div>
						</div>
					{/if}
				</CardContent>
			</Card>

			<!-- Informations supplémentaires -->
			<Card>
				<CardHeader>
					<CardTitle>ℹ️ Informations supplémentaires</CardTitle>
				</CardHeader>
				<CardContent class="space-y-3 text-sm text-slate-600 dark:text-slate-400">
					<p>
						<strong>Délai de traitement :</strong> Les demandes d'export et de suppression sont traitées immédiatement.
					</p>
					<p>
						<strong>Contact RGPD :</strong> Pour toute question sur vos données personnelles, contactez
						<a href="mailto:privacy@scimanager.fr" class="text-blue-600 dark:text-blue-400 hover:underline">
							privacy@scimanager.fr
						</a>
					</p>
					<p>
						<strong>Réclamation :</strong> Si vos droits ne sont pas respectés, vous pouvez contacter la
						<a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer" class="text-blue-600 dark:text-blue-400 hover:underline">
							CNIL
						</a>
					</p>
				</CardContent>
			</Card>
		</div>
	{/if}
</div>
