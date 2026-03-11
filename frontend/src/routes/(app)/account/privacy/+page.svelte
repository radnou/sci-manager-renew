<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import EmptyStateOperator from '$lib/components/EmptyStateOperator.svelte';
	import PageSpecificSkeleton from '$lib/components/PageSpecificSkeleton.svelte';
	import WorkspaceActionBar from '$lib/components/WorkspaceActionBar.svelte';
	import WorkspaceHeader from '$lib/components/WorkspaceHeader.svelte';
	import WorkspaceRailCard from '$lib/components/WorkspaceRailCard.svelte';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
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
	let deleteConfirmText = $state('');
	let loadError = $state('');

	onMount(async () => {
		await loadDataSummary();
	});

	async function loadDataSummary() {
		loading = true;
		loadError = '';
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
				loadError = 'Impossible de charger le résumé des données personnelles.';
				addToast({ title: 'Erreur lors du chargement du résumé des données', variant: 'error' });
			}
		} catch (error) {
			loadError = 'Erreur réseau pendant le chargement des données personnelles.';
			addToast({ title: 'Erreur réseau', variant: 'error' });
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
				const data = (await response.json()) as { export_url?: string; expires_at?: string };
				if (data.export_url) {
					window.open(data.export_url, '_blank', 'noopener,noreferrer');
					addToast({ title: 'Export prêt. Le téléchargement a été ouvert dans un nouvel onglet.', variant: 'success' });
				} else {
					addToast({ title: "Export cree, mais aucun lien de telechargement n'a ete retourne.", variant: 'error' });
				}
			} else {
				addToast({ title: 'Erreur lors de l\'export des données', variant: 'error' });
			}
		} catch (error) {
			addToast({ title: 'Erreur réseau', variant: 'error' });
			console.error(error);
		} finally {
			exportLoading = false;
		}
	}

	async function deleteAccount() {
		if (deleteConfirmText !== 'SUPPRIMER') {
			addToast({ title: 'Veuillez taper "SUPPRIMER" pour confirmer', variant: 'error' });
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
				addToast({ title: 'Compte supprimé avec succès. Redirection...', variant: 'success' });
				await supabase.auth.signOut();
				setTimeout(() => goto('/'), 2000);
			} else {
				addToast({ title: 'Erreur lors de la suppression du compte', variant: 'error' });
			}
		} catch (error) {
			addToast({ title: 'Erreur réseau', variant: 'error' });
			console.error(error);
		} finally {
			deleteLoading = false;
		}
	}
</script>

<svelte:head>
	<title>Mes Données Personnelles - GererSCI</title>
</svelte:head>

<section class="sci-page-shell">
	<WorkspaceHeader
		eyebrow="Confidentialité • droits RGPD"
		title="Données et confidentialité"
		subtitle="Export, transparence et suppression du compte passent par ce workspace. L'objectif est de garder les demandes RGPD lisibles et traçables, sans les perdre dans les préférences locales."
		contextLabel="Compte concerné"
		contextValue={dataSummary?.email || 'Session connectée'}
		contextDetail={dataSummary
			? `${dataSummary.data_summary.sci_count} SCI • ${dataSummary.data_summary.biens_count} biens • ${dataSummary.data_summary.loyers_count} loyers`
			: 'Les demandes RGPD portent sur l’ensemble des données rattachées au compte.'}
	>
		<Button onclick={exportData} disabled={exportLoading}>
			{exportLoading ? 'Export en cours...' : 'Exporter mes données'}
		</Button>
		<Button href="/account" variant="outline">Retour au compte</Button>
	</WorkspaceHeader>

	{#if loading}
		<PageSpecificSkeleton
			mode="hub"
			eyebrow="Chargement confidentialité"
			title="Préparation des données personnelles"
			description="On consolide le résumé du compte, les volumes stockés et les actions RGPD disponibles."
		/>
	{:else if !dataSummary}
		<EmptyStateOperator
			eyebrow="Résumé indisponible"
			title="Impossible de charger les données personnelles"
			description={loadError || "Le résumé RGPD n'a pas pu être récupéré. Reviens au compte ou recharge la page."}
			primaryHref="/account"
			primaryLabel="Retour au compte"
			secondaryHref="/dashboard"
			secondaryLabel="Retour au cockpit"
		/>
	{:else}
		<WorkspaceActionBar
			eyebrow="Cadre RGPD"
			title="Transparence, portabilité, suppression"
			description="Commence par la lecture du périmètre stocké, puis exporte les données si besoin. La suppression du compte reste une action séparée et explicitement confirmée."
		>
			<div class="sci-action-grid">
				<div class="sci-action-card">
					<p class="sci-action-card-title">Périmètre stocké</p>
					<p class="sci-action-card-value">{dataSummary.data_summary.sci_count} SCI • {dataSummary.data_summary.biens_count} biens</p>
					<p class="sci-action-card-body">Le résumé agrège les données principales rattachées au compte.</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Portabilité</p>
					<p class="sci-action-card-value">Export JSON immédiat</p>
					<p class="sci-action-card-body">Télécharge une copie structurée des données personnelles et métier.</p>
				</div>
				<div class="sci-action-card">
					<p class="sci-action-card-title">Suppression</p>
					<p class="sci-action-card-value">Confirmation explicite requise</p>
					<p class="sci-action-card-body">La suppression du compte reste irréversible et séparée des autres actions.</p>
				</div>
			</div>
			<div class="mt-5 sci-primary-actions">
				<Button onclick={exportData} disabled={exportLoading}>
					{exportLoading ? 'Export en cours...' : 'Exporter mes données'}
				</Button>
				<Button href="/account" variant="outline">Ouvrir le compte</Button>
				<Button href="/dashboard" variant="outline">Retour au cockpit</Button>
			</div>
			{#snippet aside()}
				<WorkspaceRailCard
					title="Support et recours"
					description="Canal RGPD direct et recours externe si les droits du compte ne sont pas respectés."
				>
					<div class="space-y-3 text-sm text-slate-500 dark:text-slate-400">
						<div class="sci-action-card">
							<p class="sci-action-card-title">Contact RGPD</p>
							<p class="sci-action-card-value">
								<a href="mailto:privacy@gerersci.fr" class="text-cyan-300 underline-offset-4 hover:underline">
									privacy@gerersci.fr
								</a>
							</p>
						</div>
						<div class="sci-action-card">
							<p class="sci-action-card-title">Autorité de contrôle</p>
							<p class="sci-action-card-value">
								<a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer" class="text-cyan-300 underline-offset-4 hover:underline">
									CNIL
								</a>
							</p>
						</div>
					</div>
				</WorkspaceRailCard>
			{/snippet}
		</WorkspaceActionBar>

		<div class="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
			<Card class="sci-section-card">
				<CardHeader>
					<CardTitle>Résumé des données</CardTitle>
					<CardDescription>Vue d'ensemble des informations stockées sur le compte connecté.</CardDescription>
				</CardHeader>
				<CardContent class="grid gap-4 pt-0 md:grid-cols-2">
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
				</CardContent>
			</Card>

			<Card class="sci-section-card border-red-200 dark:border-red-900">
				<CardHeader>
					<CardTitle class="text-red-600 dark:text-red-400">Suppression du compte</CardTitle>
					<CardDescription>Droit à l'effacement avec confirmation explicite.</CardDescription>
				</CardHeader>
				<CardContent class="space-y-4">
					<div class="rounded-2xl bg-red-50 p-4 dark:bg-red-900/20">
						<p class="mb-2 text-sm font-semibold text-red-800 dark:text-red-300">
							Attention : action irréversible
						</p>
						<p class="text-sm text-red-700 dark:text-red-400">
							La suppression du compte entraîne l'effacement définitif des SCI, biens, loyers, charges et données fiscales rattachés au compte.
						</p>
						<p class="mt-3 text-xs text-red-600 dark:text-red-500">
							Les données de facturation restent anonymisées pour répondre aux obligations légales de conservation.
						</p>
					</div>

					{#if !showDeleteConfirm}
						<Button variant="destructive" onclick={() => (showDeleteConfirm = true)}>
							Supprimer définitivement mon compte
						</Button>
					{:else}
						<div class="space-y-3 border-l-4 border-red-500 pl-4">
							<p class="text-sm font-semibold">Tape "SUPPRIMER" pour confirmer.</p>
							<input
								type="text"
								bind:value={deleteConfirmText}
								placeholder="SUPPRIMER"
								class="w-full max-w-xs rounded-md border border-slate-300 px-3 py-2 dark:border-slate-700"
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
		</div>
	{/if}
</section>
