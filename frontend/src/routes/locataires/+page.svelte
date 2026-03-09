<script lang="ts">
	import { Users } from 'lucide-svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import { Card, CardContent, CardHeader, CardTitle } from '$lib/components/ui/card';
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Gestion locative</p>
		<h1 class="sci-page-title">Locataires</h1>
		<p class="sci-page-subtitle">
			Suivi des locataires rattachés à vos biens immobiliers.
		</p>
	</header>

	<Card class="sci-section-card">
		<CardHeader>
			<CardTitle class="flex items-center gap-2 text-lg">
				<Users class="h-5 w-5 text-indigo-600" />
				Annuaire locataires
			</CardTitle>
		</CardHeader>
		<CardContent>
			<EmptyState
				title="Module locataires en préparation"
				description="La gestion complète des locataires (fiches, baux, historique) sera disponible prochainement. Les loyers sont déjà rattachés aux biens depuis le cockpit."
				ctaText="Voir les loyers"
				ctaHref="/loyers"
			/>
		</CardContent>
	</Card>
</section>
