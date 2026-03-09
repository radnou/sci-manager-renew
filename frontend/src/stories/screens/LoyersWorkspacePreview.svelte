<script lang="ts">
	import KpiCard from '$lib/components/KPI-Card.svelte';
	import LoyerForm from '$lib/components/LoyerForm.svelte';
	import LoyerTable from '$lib/components/LoyerTable.svelte';
	import QuitusGenerator from '$lib/components/QuitusGenerator.svelte';

	const loyers = [
		{ id_bien: 'BIEN-001', date_loyer: '2026-03-01', montant: 1450, statut: 'paye' },
		{ id_bien: 'BIEN-003', date_loyer: '2026-03-01', montant: 980, statut: 'en_attente' },
		{ id_bien: 'BIEN-002', date_loyer: '2026-02-28', montant: 1275, statut: 'retard' }
	];

	const noop = async () => true;
	const mockGenerateQuitus = async () =>
		new Blob(['%PDF-1.4\n% quittus\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'], {
			type: 'application/pdf'
		});
</script>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">Screen Preview</p>
		<h1 class="sci-page-title">Espace Loyers</h1>
		<p class="sci-page-subtitle">Vue intégrée des paiements, de la saisie et des quittances.</p>
	</header>

	<div class="grid gap-4 md:grid-cols-3">
		<KpiCard
			label="Encaissements"
			value="3 705 €"
			caption="période courante"
			trend="up"
			trendValue="+4.8%"
			tone="success"
		/>
		<KpiCard
			label="Ticket moyen"
			value="1 235 €"
			caption="par loyer"
			trend="neutral"
			trendValue="stable"
			tone="accent"
		/>
		<KpiCard
			label="Retards"
			value={1}
			caption="à traiter"
			trend="down"
			trendValue="attention"
			tone="warning"
		/>
	</div>

	<div class="grid gap-6 xl:grid-cols-[2fr_1fr]">
		<LoyerForm onSubmit={noop} />
		<QuitusGenerator generateQuitus={mockGenerateQuitus} />
	</div>

	<LoyerTable {loyers} />
</section>
