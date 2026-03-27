<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button';
</script>

<div class="flex min-h-[50vh] flex-col items-center justify-center px-4 text-center">
	<h1 class="text-5xl font-bold text-muted-foreground">{page.status}</h1>

	{#if page.status === 404}
		<p class="mt-4 text-lg text-muted-foreground">Cette ressource est introuvable</p>
		<p class="mt-2 text-sm text-muted-foreground">
			La SCI, le bien ou la page demandée n'existe pas ou a été supprimée.
		</p>
	{:else if page.status === 403}
		<p class="mt-4 text-lg text-muted-foreground">Accès refusé</p>
		<p class="mt-2 text-sm text-muted-foreground">
			Vous n'avez pas les droits nécessaires pour accéder à cette ressource.
		</p>
	{:else if page.status === 402}
		<p class="mt-4 text-lg text-muted-foreground">Abonnement requis</p>
		<p class="mt-2 text-sm text-muted-foreground">
			Cette fonctionnalité nécessite un abonnement actif.
		</p>
		<div class="mt-8">
			<Button href="/pricing">Voir les offres</Button>
		</div>
	{:else}
		<p class="mt-4 text-lg text-muted-foreground">
			{page.error?.message || 'Une erreur est survenue.'}
		</p>
	{/if}

	{#if page.status !== 402}
		<div class="mt-8 flex gap-4">
			<Button href="/dashboard" variant="outline">Tableau de bord</Button>
			<Button onclick={() => history.back()}>Retour</Button>
		</div>
	{/if}
</div>
