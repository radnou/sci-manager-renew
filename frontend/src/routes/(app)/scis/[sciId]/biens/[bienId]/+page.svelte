<script lang="ts">
	import { page } from '$app/state';
	import { getContext } from 'svelte';
	import type { SCIDetail, FicheBien } from '$lib/api';
	import { breadcrumbNames } from '$lib/stores/breadcrumb-names';
	import { fetchFicheBien, renderQuitus, type QuitusRequestPayload } from '$lib/api';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import FicheBienHeader from '$lib/components/fiche-bien/FicheBienHeader.svelte';
	import FicheBienIdentite from '$lib/components/fiche-bien/FicheBienIdentite.svelte';
	import FicheBienBail from '$lib/components/fiche-bien/FicheBienBail.svelte';
	import FicheBienLoyers from '$lib/components/fiche-bien/FicheBienLoyers.svelte';
	import FicheBienCharges from '$lib/components/fiche-bien/FicheBienCharges.svelte';
	import FicheBienRentabilite from '$lib/components/fiche-bien/FicheBienRentabilite.svelte';
	import FicheBienDocuments from '$lib/components/fiche-bien/FicheBienDocuments.svelte';
	import { Home, FileSignature, Receipt, Wallet, TrendingUp, FolderOpen } from 'lucide-svelte';

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
		{ id: 'rentabilite', label: 'Rentabilité', icon: TrendingUp },
		{ id: 'documents', label: 'Documents', icon: FolderOpen }
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

	function scrollToSection(id: string) {
		activeSection = id;
		const el = document.getElementById(`section-${id}`);
		if (el) {
			const offset = 160;
			const top = el.getBoundingClientRect().top + window.scrollY - offset;
			window.scrollTo({ top, behavior: 'smooth' });
		}
	}

	async function handleGenerateQuittance() {
		if (!bien?.bail_actif?.locataires?.length) {
			addToast({ title: 'Aucun locataire associé au bail', variant: 'error' });
			return;
		}
		const lastPaidLoyer = [...(bien.loyers_recents ?? [])].reverse().find((l: any) => l.statut === 'paye');
		if (!lastPaidLoyer) {
			addToast({ title: 'Aucun loyer payé pour générer une quittance', variant: 'error' });
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

<svelte:head><title>{bien?.adresse ?? 'Bien'} | GererSCI</title></svelte:head>

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

		<!-- Section navigation (sticky) -->
		<nav class="sticky top-[var(--navbar-height,3.5rem)] z-30 -mx-4 mt-4 border-b border-slate-200 bg-white/95 backdrop-blur-md md:-mx-8 dark:border-slate-800 dark:bg-slate-950/95">
			<div class="flex gap-0 overflow-x-auto px-4 md:px-8">
				{#each sections as sec (sec.id)}
					<button
						type="button"
						onclick={() => scrollToSection(sec.id)}
						class="relative flex items-center gap-1.5 whitespace-nowrap px-3.5 py-3 text-sm font-medium transition-colors {activeSection === sec.id
							? 'text-blue-600 dark:text-blue-400'
							: 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'}"
					>
						<sec.icon class="h-4 w-4" />
						<span>{sec.label}</span>
						{#if activeSection === sec.id}
							<span class="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-blue-600 dark:bg-blue-400"></span>
						{/if}
					</button>
				{/each}
			</div>
		</nav>

		<div class="sci-stagger mt-6 space-y-6">
			<div id="section-identite">
				<FicheBienIdentite {bien} {isGerant} onRefresh={loadFicheBien} />
			</div>
			<div id="section-bail">
				<FicheBienBail bail={bien.bail_actif} {isGerant} sciId={sciId} bienId={String(bien.id)} onRefresh={loadFicheBien} />
			</div>
			<div id="section-loyers">
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
			<div id="section-charges">
				<FicheBienCharges
					charges={bien.charges_list}
					assurancePno={bien.assurance_pno}
					fraisAgence={bien.frais_agence}
					{isGerant}
					sciId={sciId}
					bienId={String(bien.id)}
					onRefresh={loadFicheBien}
				/>
			</div>
			<div id="section-rentabilite">
				<FicheBienRentabilite rentabilite={bien.rentabilite} />
			</div>
			<div id="section-documents">
				<FicheBienDocuments
					documents={bien.documents}
					{isGerant}
					sciId={sciId}
					bienId={String(bien.id)}
				/>
			</div>
		</div>
	{/if}
</section>
