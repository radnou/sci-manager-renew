<script lang="ts">
	import { page } from '$app/state';
	import { onMount, getContext } from 'svelte';
	import type { SCIDetail, FicheBien } from '$lib/api';
	import { breadcrumbNames } from '$lib/stores/breadcrumb-names';
	import { fetchFicheBien, renderQuitus, type QuitusRequestPayload } from '$lib/api';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import FicheBienHeader from '$lib/components/fiche-bien/FicheBienHeader.svelte';
	import FicheBienIdentite from '$lib/components/fiche-bien/FicheBienIdentite.svelte';
	import FicheBienBail from '$lib/components/fiche-bien/FicheBienBail.svelte';
	import FicheBienLoyers from '$lib/components/fiche-bien/FicheBienLoyers.svelte';
	import FicheBienCharges from '$lib/components/fiche-bien/FicheBienCharges.svelte';
	import FicheBienPno from '$lib/components/fiche-bien/FicheBienPno.svelte';
	import FicheBienAgence from '$lib/components/fiche-bien/FicheBienAgence.svelte';
	import FicheBienRentabilite from '$lib/components/fiche-bien/FicheBienRentabilite.svelte';
	import FicheBienDocuments from '$lib/components/fiche-bien/FicheBienDocuments.svelte';
	import FicheBienEvenements from '$lib/components/fiche-bien/FicheBienEvenements.svelte';
	import { Home, FileSignature, Receipt, Wallet, Shield, Building2, TrendingUp, FolderOpen, CalendarClock } from 'lucide-svelte';

	const sci = getContext<SCIDetail>('sci');
	const userRole = getContext<string>('userRole');

	let sciId = $derived(page.params.sciId!);
	let bienId = $derived(page.params.bienId!);
	let isGerant = $derived(userRole === 'gerant');

	let nomLocataire = $derived.by(() => {
		if (!bien?.bail_actif?.locataires?.length) return '';
		const loc = bien.bail_actif.locataires[0];
		return [loc.prenom, loc.nom].filter(Boolean).join(' ');
	});

	let bien: FicheBien | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);
	let activeSection = $state('identite');
	let generatingQuittance = $state(false);

	const sections = [
		{ id: 'identite', label: 'Identité', icon: Home },
		{ id: 'bail', label: 'Bail', icon: FileSignature },
		{ id: 'loyers', label: 'Loyers', icon: Receipt },
		{ id: 'charges', label: 'Charges', icon: Wallet },
		{ id: 'pno', label: 'Assurance PNO', icon: Shield },
		{ id: 'agence', label: 'Agence', icon: Building2 },
		{ id: 'rentabilite', label: 'Rentabilité', icon: TrendingUp },
		{ id: 'documents', label: 'Documents', icon: FolderOpen },
		{ id: 'evenements', label: 'Événements', icon: CalendarClock }
	];

	$effect(() => {
		if (sciId && bienId) {
			loadFicheBien();
		}
	});

	async function loadFicheBien() {
		loading = true;
		error = null;
		try {
			bien = await fetchFicheBien(sciId, bienId);
			if (bien?.adresse) {
				breadcrumbNames.update((n) => ({ ...n, [bienId]: bien!.adresse }));
			}
		} catch (err: any) {
			error = err?.message ?? 'Impossible de charger les données du bien.';
			bien = null;
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		const hash = window.location.hash?.replace('#', '');
		if (hash && sections.some((section) => section.id === hash)) {
			activeSection = hash;
		}
	});

	function scrollToSection(id: string) {
		activeSection = id;
		if (typeof window !== 'undefined') {
			const nextUrl = `${window.location.pathname}#${id}`;
			window.history.replaceState(window.history.state, '', nextUrl);
		}
	}

	async function handleGenerateQuittance() {
		if (!bien?.bail_actif) {
			addToast({
				title: 'Aucun bail actif',
				description: "Créez d'abord un bail actif pour ce bien avant de générer une quittance.",
				variant: 'error'
			});
			return;
		}
		if (!bien.bail_actif.locataires?.length) {
			addToast({
				title: 'Aucun locataire associé au bail',
				description: 'Rattachez un locataire au bail actif avant de générer une quittance.',
				variant: 'error'
			});
			return;
		}
		const lastPaidLoyer = [...(bien.loyers_recents ?? [])].reverse().find((l: any) => l.statut === 'paye');
		if (!lastPaidLoyer) {
			addToast({
				title: 'Aucun loyer payé',
				description: "Enregistrez au moins un loyer payé pour générer une quittance.",
				variant: 'error'
			});
			return;
		}
		generatingQuittance = true;
		try {
			const payload: QuitusRequestPayload = {
				id_loyer: lastPaidLoyer.id,
				id_bien: bien.id,
				nom_locataire: nomLocataire,
				periode: lastPaidLoyer.date_loyer ?? new Date().toISOString().slice(0, 7),
				montant: lastPaidLoyer.montant ?? 0,
				nom_sci: sci.nom,
				adresse_bien: bien.adresse,
				ville_bien: bien.ville ?? ''
			};
			const blob = await renderQuitus(payload);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `quittance_${bien.adresse.replace(/\s+/g, '_')}.pdf`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			addToast({ title: 'Quittance générée', description: 'Le PDF a été téléchargé.', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de générer la quittance.', variant: 'error' });
		} finally {
			generatingQuittance = false;
		}
	}
</script>

<svelte:head><title>{bien?.adresse ?? 'Bien'} | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	{#if loading}
		<div class="sci-loading" aria-label="Chargement"></div>
	{:else if error}
		<header class="sci-page-header">
			<p class="sci-eyebrow">{sci.nom} / Biens</p>
			<h1 class="sci-page-title">Erreur</h1>
		</header>
		<div class="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30">
			<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
			<button
				onclick={loadFicheBien}
				class="mt-3 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400"
			>
				Réessayer
			</button>
		</div>
	{:else if bien}
		<FicheBienHeader
			{bien}
			sciNom={sci.nom}
			{isGerant}
			onGenerateQuittance={handleGenerateQuittance}
			{generatingQuittance}
		/>

		<nav
			class="mt-4 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm dark:border-slate-800 dark:bg-slate-950"
			aria-label="Sections de la fiche bien"
		>
			<div class="flex gap-2 overflow-x-auto" role="tablist" aria-label="Navigation fiche bien">
				{#each sections as sec (sec.id)}
					<button
						type="button"
						onclick={() => scrollToSection(sec.id)}
						role="tab"
						aria-selected={activeSection === sec.id}
						class="relative flex items-center gap-1.5 whitespace-nowrap rounded-xl px-3.5 py-2.5 text-sm font-medium transition-colors {activeSection === sec.id
							? 'bg-sky-600 text-white shadow-sm'
							: 'text-slate-500 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white'}"
					>
						<sec.icon class="h-4 w-4" />
						<span>{sec.label}</span>
					</button>
				{/each}
			</div>
		</nav>

		<div class="sci-stagger mt-6">
			{#if activeSection === 'identite'}
			<div id="section-identite" role="tabpanel" aria-label="Identité">
				<FicheBienIdentite {bien} {isGerant} onRefresh={loadFicheBien} />
			</div>
			{:else if activeSection === 'bail'}
			<div id="section-bail" role="tabpanel" aria-label="Bail">
				<FicheBienBail bail={bien.bail_actif} loyers={bien.loyers_recents} {isGerant} sciId={sciId} bienId={String(bien.id)} onRefresh={loadFicheBien} />
			</div>
			{:else if activeSection === 'loyers'}
			<div id="section-loyers" role="tabpanel" aria-label="Loyers">
				<FicheBienLoyers
					loyers={bien.loyers_recents}
					{isGerant}
					{sciId}
					{bienId}
					{nomLocataire}
					nomSci={sci.nom}
					adresseBien={bien.adresse}
					villeBien={bien.ville}
					onRefresh={loadFicheBien}
				/>
			</div>
			{:else if activeSection === 'charges'}
			<div id="section-charges" role="tabpanel" aria-label="Charges">
				<FicheBienCharges
					charges={bien.charges_list}
					{isGerant}
					sciId={sciId}
					bienId={String(bien.id)}
					onRefresh={loadFicheBien}
				/>
			</div>
			{:else if activeSection === 'pno'}
			<div id="section-pno" role="tabpanel" aria-label="Assurance PNO">
				<FicheBienPno
					assurancePno={bien.assurance_pno}
					{isGerant}
					sciId={sciId}
					bienId={String(bien.id)}
					onRefresh={loadFicheBien}
				/>
			</div>
			{:else if activeSection === 'agence'}
			<div id="section-agence" role="tabpanel" aria-label="Agence">
				<FicheBienAgence
					fraisAgence={bien.frais_agence}
					{isGerant}
					sciId={sciId}
					bienId={String(bien.id)}
					onRefresh={loadFicheBien}
				/>
			</div>
			{:else if activeSection === 'rentabilite'}
			<div id="section-rentabilite" role="tabpanel" aria-label="Rentabilité">
				<FicheBienRentabilite rentabilite={bien.rentabilite} hasSourceData={bien.prix_acquisition != null && bien.bail_actif != null} {sciId} {bienId} />
			</div>
			{:else if activeSection === 'documents'}
			<div id="section-documents" role="tabpanel" aria-label="Documents">
				<FicheBienDocuments
					documents={bien.documents}
					{isGerant}
					sciId={sciId}
					bienId={String(bien.id)}
				/>
			</div>
			{:else if activeSection === 'evenements'}
			<div id="section-evenements" role="tabpanel" aria-label="Événements">
				<FicheBienEvenements
					{isGerant}
					sciId={sciId}
					bienId={String(bien.id)}
				/>
			</div>
			{/if}
		</div>
	{/if}
</section>
