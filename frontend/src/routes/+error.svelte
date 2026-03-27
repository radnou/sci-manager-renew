<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button';
</script>

<div class="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
	<h1 class="text-6xl font-bold text-muted-foreground">{page.status}</h1>

	{#if page.status === 404}
		<p class="mt-4 text-xl text-muted-foreground">Page introuvable</p>
		<p class="mt-2 text-sm text-muted-foreground">
			La page que vous recherchez n'existe pas ou a été déplacée.
		</p>
	{:else if page.status === 500}
		<p class="mt-4 text-xl text-muted-foreground">Erreur serveur</p>
		<p class="mt-2 text-sm text-muted-foreground">
			Une erreur inattendue s'est produite. Veuillez réessayer dans quelques instants.
		</p>
	{:else if page.status === 503}
		<p class="mt-4 text-xl text-muted-foreground">Service indisponible</p>
		<p class="mt-2 text-sm text-muted-foreground">
			GérerSCI est en cours de maintenance. Revenez dans quelques minutes.
		</p>
	{:else}
		<p class="mt-4 text-xl text-muted-foreground">Erreur {page.status}</p>
		<p class="mt-2 text-sm text-muted-foreground">
			{page.error?.message || 'Une erreur est survenue.'}
		</p>
	{/if}

	<div class="mt-8 flex gap-4">
		<Button href="/" variant="outline">Accueil</Button>
		<Button href="/dashboard">Tableau de bord</Button>
	</div>
</div>
