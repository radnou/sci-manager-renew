<script lang="ts">
	import BienForm from '$lib/components/BienForm.svelte';
	import BienTable from '$lib/components/BienTable.svelte';
	import KpiCard from '$lib/components/KPI-Card.svelte';

	const biens = [
		{ adresse: '14 rue Saint-Honoré', ville: 'Paris', loyer_cc: 1450, statut: 'occupe' },
		{ adresse: '8 avenue des Tilleuls', ville: 'Lyon', loyer_cc: 980, statut: 'vacant' },
		{ adresse: '21 quai Richelieu', ville: 'Bordeaux', loyer_cc: 1275, statut: 'occupe' }
	];

	const noop = async () => true;
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Screen Preview</p>
		<h1 class="sci-page-title">Espace Biens</h1>
		<p class="sci-page-subtitle">Composition complète: KPIs, formulaire d’ajout et tableau des actifs.</p>
	</header>

	<div class="grid gap-4 md:grid-cols-3">
		<KpiCard label="Biens" value={3} caption="portefeuille" trend="up" trendValue="+1" tone="accent" />
		<KpiCard
			label="Loyer mensuel"
			value="3 705 €"
			caption="charges comprises"
			trend="up"
			trendValue="+4%"
			tone="success"
		/>
		<KpiCard label="Occupation" value="67%" caption="2/3 biens occupés" trend="neutral" trendValue="stable" />
	</div>

	<BienForm onSubmit={noop} />
	<BienTable {biens} />
</section>
