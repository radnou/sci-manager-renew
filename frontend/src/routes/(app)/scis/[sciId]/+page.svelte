<script lang="ts">
	import { getContext } from 'svelte';
	import { Building2, Users, FileText, MapPin, FolderOpen, Download } from 'lucide-svelte';
	import type { SCIDetail } from '$lib/api';
	import { fetchSciBiensList, exportBiensCsv, exportLoyersCsv } from '$lib/api';
	import { Button } from '$lib/components/ui/button';
	import { addToast } from '$lib/components/ui/toast';

	const sci = getContext<SCIDetail>('sci');
	const sciId = getContext<string>('sciId');
	const userRole = getContext<string>('userRole');

	let biensCount = $state(sci.biens_count ?? sci.biens?.length ?? 0);
	let loadingBiens = $state(false);
	let exportingBiens = $state(false);
	let exportingLoyers = $state(false);

	async function handleExportBiens() {
		exportingBiens = true;
		try {
			const blob = await exportBiensCsv();
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `biens_export_${new Date().toISOString().slice(0, 10)}.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			addToast({ title: 'Export termine', description: 'Le fichier CSV des biens a ete telecharge.', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur export', description: err?.message ?? "Impossible d'exporter les biens.", variant: 'error' });
		} finally {
			exportingBiens = false;
		}
	}

	async function handleExportLoyers() {
		exportingLoyers = true;
		try {
			const blob = await exportLoyersCsv();
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `loyers_export_${new Date().toISOString().slice(0, 10)}.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			addToast({ title: 'Export termine', description: 'Le fichier CSV des loyers a ete telecharge.', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur export', description: err?.message ?? "Impossible d'exporter les loyers.", variant: 'error' });
		} finally {
			exportingLoyers = false;
		}
	}

	$effect(() => {
		if (biensCount === 0 && !sci.biens_count) {
			loadBiensCount();
		}
	});

	async function loadBiensCount() {
		loadingBiens = true;
		try {
			const list = await fetchSciBiensList(sciId);
			biensCount = list.length;
		} catch {
			// keep the default count
		} finally {
			loadingBiens = false;
		}
	}

	const quickLinks = $derived([
		{
			href: `/scis/${sciId}/biens`,
			icon: MapPin,
			iconClass: 'text-blue-600',
			value: biensCount,
			label: 'Biens',
			loading: loadingBiens
		},
		{
			href: `/scis/${sciId}/associes`,
			icon: Users,
			iconClass: 'text-purple-600',
			value: sci.associes_count ?? sci.associes?.length ?? 0,
			label: 'Associés',
			loading: false
		},
		{
			href: `/scis/${sciId}/fiscalite`,
			icon: FileText,
			iconClass: 'text-amber-600',
			value: sci.regime_fiscal ?? '—',
			label: 'Régime fiscal',
			loading: false
		},
		{
			href: `/scis/${sciId}/documents`,
			icon: FolderOpen,
			iconClass: 'text-teal-600',
			value: sci.fiscalite?.length ?? 0,
			label: 'Documents',
			loading: false
		}
	]);
</script>

<svelte:head><title>{sci.nom} | GererSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">SCI</p>
		<h1 class="sci-page-title">{sci.nom}</h1>
		{#if sci.siren}
			<p class="text-sm text-slate-500 dark:text-slate-400">SIREN: {sci.siren}</p>
		{/if}
	</header>

	<div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#each quickLinks as link}
			<a
				href={link.href}
				class="group rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950 dark:hover:border-slate-700"
			>
				<link.icon class="h-6 w-6 {link.iconClass}" />
				<p class="mt-3 text-2xl font-bold text-slate-900 dark:text-slate-100">
					{#if link.loading}
						<span class="inline-flex h-7 w-10 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></span>
					{:else}
						{link.value}
					{/if}
				</p>
				<p class="text-sm text-slate-500 dark:text-slate-400">{link.label}</p>
			</a>
		{/each}
	</div>

	<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<div class="flex items-center gap-3">
			<Building2 class="h-5 w-5 text-emerald-600" />
			<div>
				<p class="text-sm font-medium text-slate-900 dark:text-slate-100">
					Votre rôle : {userRole === 'gerant' ? 'Gérant' : 'Associé'}
				</p>
				{#if sci.user_part != null}
					<p class="text-xs text-slate-500 dark:text-slate-400">
						Part détenue : {sci.user_part}%
					</p>
				{/if}
			</div>
		</div>
		{#if sci.statut}
			<p class="mt-3 text-xs text-slate-500 dark:text-slate-400">
				Statut :
				{#if sci.statut === 'configuration'}
					À structurer
				{:else if sci.statut === 'mise_en_service'}
					Mise en service
				{:else}
					En exploitation
				{/if}
			</p>
		{/if}
	</div>

	<div class="mt-6 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
		<h2 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Exports</h2>
		<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">Telecharger les donnees de cette SCI au format CSV.</p>
		<div class="mt-4 flex flex-wrap items-center gap-3">
			<Button onclick={handleExportBiens} disabled={exportingBiens} variant="outline">
				<Download class="mr-2 h-4 w-4" />
				{exportingBiens ? 'Export en cours...' : 'Exporter les biens (CSV)'}
			</Button>
			<Button onclick={handleExportLoyers} disabled={exportingLoyers} variant="outline">
				<Download class="mr-2 h-4 w-4" />
				{exportingLoyers ? 'Export en cours...' : 'Exporter les loyers (CSV)'}
			</Button>
		</div>
	</div>
</section>
