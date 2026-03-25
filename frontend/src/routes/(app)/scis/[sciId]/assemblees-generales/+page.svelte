<script lang="ts">
	import { getContext } from 'svelte';
	import type { AssembleeGenerale, AssembleeGeneraleInput, SCIDetail } from '$lib/api';
	import {
		createAssembleeGenerale,
		deleteAssembleeGenerale,
		fetchAssembleesGenerales,
		updateAssembleeGenerale,
		fetchAgModele,
		genererConvocation
	} from '$lib/api';
	import type { ConvocationResult } from '$lib/api';
	import { formatFrDate } from '$lib/high-value/formatters';
	import { addToast } from '$lib/components/ui/toast/toast-store';
	import { CalendarDays, CheckCircle2, ClipboardList, FileText, Pencil, Plus, Trash2, Send, Copy, Download, X, Loader2 } from 'lucide-svelte';
	import RoleGate from '$lib/components/RoleGate.svelte';

	const sci = getContext<SCIDetail>('sci');
	const userRole = getContext<string>('userRole');
	const isGerant = $derived(userRole === 'gerant');

	type EditorState = AssembleeGeneraleInput;

	const EMPTY_EDITOR: EditorState = {
		date_ag: '',
		type_ag: 'ordinaire',
		exercice_annee: new Date().getFullYear() - 1,
		ordre_du_jour: '',
		pv_url: '',
		quorum_atteint: false,
		resolutions: '',
		notes: ''
	};

	let assemblees: AssembleeGenerale[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);
	let editorOpen = $state(false);
	let saving = $state(false);
	let deletingId: string | null = $state(null);
	let editingId: string | null = $state(null);
	let editor: EditorState = $state({ ...EMPTY_EDITOR });
	let initialized = false;

	const nextAg = $derived(
		assemblees
			.filter((ag) => new Date(ag.date_ag).getTime() >= Date.now() - 24 * 60 * 60 * 1000)
			.sort((a, b) => a.date_ag.localeCompare(b.date_ag))[0] ?? null
	);
	const completedQuorumCount = $derived(assemblees.filter((ag) => ag.quorum_atteint).length);

	$effect(() => {
		if (initialized) {
			return;
		}
		initialized = true;
		loadData();
	});

	async function loadData() {
		loading = true;
		error = null;
		try {
			assemblees = await fetchAssembleesGenerales(sci.id);
		} catch {
			error = "Impossible de charger le registre des assemblées générales.";
		} finally {
			loading = false;
		}
	}

	function resetEditor() {
		editor = { ...EMPTY_EDITOR };
		editingId = null;
	}

	function openCreateEditor() {
		resetEditor();
		editorOpen = true;
	}

	function openEditEditor(ag: AssembleeGenerale) {
		editor = {
			date_ag: ag.date_ag,
			type_ag: ag.type_ag,
			exercice_annee: ag.exercice_annee,
			ordre_du_jour: ag.ordre_du_jour ?? '',
			pv_url: ag.pv_url ?? '',
			quorum_atteint: ag.quorum_atteint,
			resolutions: ag.resolutions ?? '',
			notes: ag.notes ?? ''
		};
		editingId = String(ag.id);
		editorOpen = true;
	}

	function closeEditor() {
		editorOpen = false;
		resetEditor();
	}

	function normalizeEditor(): AssembleeGeneraleInput {
		return {
			date_ag: editor.date_ag,
			type_ag: editor.type_ag,
			exercice_annee: Number(editor.exercice_annee),
			ordre_du_jour: editor.ordre_du_jour?.trim() || null,
			pv_url: editor.pv_url?.trim() || null,
			quorum_atteint: editor.quorum_atteint,
			resolutions: editor.resolutions?.trim() || null,
			notes: editor.notes?.trim() || null
		};
	}

	async function handleSave() {
		if (!editor.date_ag) {
			addToast({
				title: 'Date requise',
				description: "Renseignez la date de l'assemblée générale.",
				variant: 'error'
			});
			return;
		}

		saving = true;
		try {
			const payload = normalizeEditor();
			if (editingId) {
				await updateAssembleeGenerale(sci.id, editingId, payload);
				addToast({
					title: 'AG mise à jour',
					description: "Le dossier d'assemblée a été mis à jour.",
					variant: 'success'
				});
			} else {
				await createAssembleeGenerale(sci.id, payload);
				addToast({
					title: 'AG créée',
					description: "L'assemblée générale a été ajoutée au registre.",
					variant: 'success'
				});
			}
			closeEditor();
			await loadData();
		} catch (err: any) {
			addToast({
				title: 'Erreur',
				description: err?.message ?? "Impossible d'enregistrer l'assemblée générale.",
				variant: 'error'
			});
		} finally {
			saving = false;
		}
	}

	async function handleDelete(ag: AssembleeGenerale) {
		deletingId = String(ag.id);
		try {
			await deleteAssembleeGenerale(sci.id, ag.id);
			addToast({
				title: 'AG supprimée',
				description: "L'assemblée générale a été retirée du registre.",
				variant: 'success'
			});
			if (editingId === String(ag.id)) {
				closeEditor();
			}
			await loadData();
		} catch (err: any) {
			addToast({
				title: 'Erreur',
				description: err?.message ?? "Impossible de supprimer l'assemblée générale.",
				variant: 'error'
			});
		} finally {
			deletingId = null;
		}
	}

	function excerpt(value: string | null | undefined, fallback: string) {
		if (!value?.trim()) {
			return fallback;
		}
		return value.trim();
	}

	function typeLabel(type: string) {
		return type === 'extraordinaire' ? 'Extraordinaire' : 'Ordinaire';
	}

	function typeBadgeClass(type: string) {
		if (type === 'extraordinaire') {
			return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300';
		}
		return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300';
	}

	// ── Modèles AG ─────────────────────────
	let loadingModele: string | null = $state(null);

	async function loadModele(type: string) {
		loadingModele = type;
		try {
			const modele = await fetchAgModele(sci.id, type);
			editor = {
				date_ag: '',
				type_ag: modele.type_ag === 'extraordinaire' ? 'extraordinaire' : 'ordinaire',
				exercice_annee: new Date().getFullYear() - 1,
				ordre_du_jour: modele.ordre_du_jour ?? '',
				pv_url: '',
				quorum_atteint: false,
				resolutions: modele.resolutions ?? '',
				notes: modele.notes ?? ''
			};
			editingId = null;
			editorOpen = true;
			addToast({ title: 'Modèle chargé', description: 'Le formulaire a été pré-rempli.', variant: 'success' });
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de charger le modèle.', variant: 'error' });
		} finally {
			loadingModele = null;
		}
	}

	// ── Convocation ─────────────────────────
	let showConvocationModal = $state(false);
	let convocationData = $state<ConvocationResult | null>(null);
	let generatingConvocation: string | null = $state(null);

	async function handleGenererConvocation(ag: AssembleeGenerale) {
		generatingConvocation = String(ag.id);
		try {
			convocationData = await genererConvocation(sci.id, ag.id);
			showConvocationModal = true;
		} catch (err: any) {
			addToast({ title: 'Erreur', description: err?.message ?? 'Impossible de générer la convocation.', variant: 'error' });
		} finally {
			generatingConvocation = null;
		}
	}

	function copyConvocation() {
		if (!convocationData) return;
		navigator.clipboard.writeText(convocationData.texte);
		addToast({ title: 'Copié', description: 'Le texte de la convocation a été copié.', variant: 'success' });
	}

	function downloadConvocation() {
		if (!convocationData) return;
		const blob = new Blob([convocationData.texte], { type: 'text/plain;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `convocation_ag_${convocationData.date_envoi}.txt`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}
</script>

<svelte:head><title>Assemblées générales | {sci.nom} | GérerSCI</title></svelte:head>

<section class="sci-page-shell">
	<header class="sci-page-header">
		<p class="sci-eyebrow">{sci.nom}</p>
		<h1 class="sci-page-title">Assemblées générales</h1>
		<p class="mt-3 max-w-3xl text-sm text-slate-600 dark:text-slate-400">
			On suit ici la préparation, les notes, les résolutions et le partage du procès-verbal.
			L'objectif n'est pas seulement d'archiver une date, mais de tenir un dossier de gouvernance exploitable.
		</p>
	</header>

	<div class="mt-6 grid gap-4 lg:grid-cols-3">
		<div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center gap-3">
				<CalendarDays class="h-5 w-5 text-sky-600 dark:text-sky-400" />
				<div>
					<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Prochaine échéance</p>
					<p class="mt-1 text-base font-semibold text-slate-900 dark:text-slate-100">
						{nextAg ? formatFrDate(nextAg.date_ag) : 'Aucune AG planifiée'}
					</p>
				</div>
			</div>
		</div>
		<div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center gap-3">
				<CheckCircle2 class="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
				<div>
					<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Quorum documenté</p>
					<p class="mt-1 text-base font-semibold text-slate-900 dark:text-slate-100">
						{completedQuorumCount} / {assemblees.length || 0} AG
					</p>
				</div>
			</div>
		</div>
		<div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center gap-3">
				<FileText class="h-5 w-5 text-violet-600 dark:text-violet-400" />
				<div>
					<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Dossier AG</p>
					<p class="mt-1 text-base font-semibold text-slate-900 dark:text-slate-100">
						Notes, résolutions et lien de partage du PV
					</p>
				</div>
			</div>
		</div>
	</div>

	<div class="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
		<div class="space-y-4">
			<div class="flex items-center justify-between">
				<div>
					<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Registre et dossiers</h2>
					<p class="text-sm text-slate-500 dark:text-slate-400">
						Chaque AG garde son ordre du jour, ses notes de séance, ses résolutions et son lien de partage.
					</p>
				</div>
				<RoleGate>
					<div class="flex items-center gap-2">
						<button
							type="button"
							class="inline-flex items-center gap-2 rounded-xl border border-emerald-200 px-3 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-50 disabled:opacity-50 dark:border-emerald-800 dark:text-emerald-300 dark:hover:bg-emerald-950/30"
							onclick={() => loadModele('ago_approbation_comptes')}
							disabled={loadingModele === 'ago_approbation_comptes'}
						>
							{#if loadingModele === 'ago_approbation_comptes'}
								<Loader2 class="h-4 w-4 animate-spin" />
							{:else}
								<ClipboardList class="h-4 w-4" />
							{/if}
							Nouvelle AGO
						</button>
						<button
							type="button"
							class="inline-flex items-center gap-2 rounded-xl border border-amber-200 px-3 py-2 text-sm font-medium text-amber-700 transition-colors hover:bg-amber-50 disabled:opacity-50 dark:border-amber-800 dark:text-amber-300 dark:hover:bg-amber-950/30"
							onclick={() => loadModele('age_modification_statuts')}
							disabled={loadingModele === 'age_modification_statuts'}
						>
							{#if loadingModele === 'age_modification_statuts'}
								<Loader2 class="h-4 w-4 animate-spin" />
							{:else}
								<FileText class="h-4 w-4" />
							{/if}
							Nouvelle AGE
						</button>
						<button
							type="button"
							class="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700"
							onclick={openCreateEditor}
						>
							<Plus class="h-4 w-4" />
							Planifier une AG
						</button>
					</div>
				</RoleGate>
			</div>

			{#if loading}
				<div class="sci-loading" aria-label="Chargement"></div>
			{:else if error}
				<div class="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-300">
					{error}
				</div>
			{:else if assemblees.length === 0}
				<div class="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center dark:border-slate-700 dark:bg-slate-950">
					<ClipboardList class="mx-auto h-8 w-8 text-slate-400 dark:text-slate-600" />
					<p class="mt-3 text-sm font-medium text-slate-900 dark:text-slate-100">
						Aucune assemblée générale enregistrée.
					</p>
					<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
						Commencez par planifier la prochaine AG, puis consignez l'ordre du jour, les notes et le lien de partage du PV.
					</p>
				</div>
			{:else}
				<div class="space-y-4">
					{#each assemblees as ag (ag.id)}
						<article class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
							<div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
								<div class="space-y-3">
									<div class="flex flex-wrap items-center gap-2">
										<span class={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${typeBadgeClass(ag.type_ag)}`}>
											{typeLabel(ag.type_ag)}
										</span>
										<span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
											Exercice {ag.exercice_annee}
										</span>
										{#if ag.quorum_atteint}
											<span class="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
												Quorum atteint
											</span>
										{:else}
											<span class="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
												Quorum à confirmer
											</span>
										{/if}
									</div>

									<div>
										<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
											{formatFrDate(ag.date_ag)}
										</h3>
										<p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
											{excerpt(ag.ordre_du_jour, "Ordre du jour non renseigné.")}
										</p>
									</div>
								</div>

								<RoleGate>
									<div class="flex items-center gap-2">
										<button
											type="button"
											class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
											onclick={() => openEditEditor(ag)}
										>
											<Pencil class="h-4 w-4" />
											Modifier
										</button>
										<button
											type="button"
											class="inline-flex items-center gap-2 rounded-xl border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 transition-colors hover:bg-rose-50 dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950/40"
											disabled={deletingId === String(ag.id)}
											onclick={() => handleDelete(ag)}
										>
											<Trash2 class="h-4 w-4" />
											Supprimer
										</button>
										<button
											type="button"
											class="inline-flex items-center gap-2 rounded-xl border border-sky-200 px-3 py-2 text-sm font-medium text-sky-700 transition-colors hover:bg-sky-50 disabled:opacity-50 dark:border-sky-800 dark:text-sky-300 dark:hover:bg-sky-950/30"
											disabled={generatingConvocation === String(ag.id)}
											onclick={() => handleGenererConvocation(ag)}
										>
											{#if generatingConvocation === String(ag.id)}
												<Loader2 class="h-4 w-4 animate-spin" />
											{:else}
												<Send class="h-4 w-4" />
											{/if}
											Convocation
										</button>
									</div>
								</RoleGate>
							</div>

							<div class="mt-5 grid gap-4 md:grid-cols-2">
								<div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
									<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Résolutions</p>
									<p class="mt-2 whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-300">
										{excerpt(ag.resolutions, 'Aucune résolution formalisée pour le moment.')}
									</p>
								</div>
								<div class="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
									<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Notes de séance</p>
									<p class="mt-2 whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-300">
										{excerpt(ag.notes, 'Aucune note opérationnelle consignée.')}
									</p>
								</div>
							</div>

							<div class="mt-4 flex flex-wrap items-center gap-3 text-sm">
								{#if ag.pv_url}
									<a
										href={ag.pv_url}
										target="_blank"
										rel="noopener noreferrer"
										class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 font-medium text-sky-700 transition-colors hover:bg-sky-50 dark:border-slate-700 dark:text-sky-300 dark:hover:bg-sky-950/30"
									>
										<FileText class="h-4 w-4" />
										Ouvrir le PV partagé
									</a>
								{:else}
									<span class="rounded-xl bg-slate-100 px-3 py-2 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
										Aucun lien de PV partagé
									</span>
								{/if}
							</div>
						</article>
					{/each}
				</div>
			{/if}
		</div>

		<div class="space-y-4">
			<div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
				<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">
					{editingId ? 'Mettre à jour le dossier AG' : 'Préparer une AG'}
				</h2>
				<p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
					L'éditeur centralise la date, l'ordre du jour, les notes prises pendant la séance, les résolutions et le lien du procès-verbal partagé.
				</p>

				{#if !editorOpen}
					<div class="mt-4 rounded-2xl border border-dashed border-slate-300 p-4 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
						{#if isGerant}
							Ouvrez l'éditeur pour préparer une prochaine AG ou compléter une séance passée.
						{:else}
							Seul un gérant peut modifier le registre, mais vous pouvez consulter les notes, résolutions et liens de partage.
						{/if}
					</div>
				{:else}
					<div class="mt-5 space-y-4">
						<div class="grid gap-4 sm:grid-cols-2">
							<label class="sci-field" for="ag-date">
								<span class="sci-field-label">Date</span>
								<input id="ag-date" type="date" class="sci-input" bind:value={editor.date_ag} />
							</label>
							<label class="sci-field" for="ag-type">
								<span class="sci-field-label">Type</span>
								<select id="ag-type" class="sci-select" bind:value={editor.type_ag}>
									<option value="ordinaire">Ordinaire</option>
									<option value="extraordinaire">Extraordinaire</option>
								</select>
							</label>
						</div>

						<div class="grid gap-4 sm:grid-cols-[0.7fr_1fr]">
							<label class="sci-field" for="ag-exercice">
								<span class="sci-field-label">Exercice</span>
								<input
									id="ag-exercice"
									type="number"
									min="2000"
									max="2100"
									class="sci-input"
									bind:value={editor.exercice_annee}
								/>
							</label>
							<label class="flex items-center gap-3 rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-700 dark:border-slate-700 dark:text-slate-200">
								<input id="ag-quorum" type="checkbox" bind:checked={editor.quorum_atteint} />
								<span>Quorum atteint et présence constatée</span>
							</label>
						</div>

						<label class="sci-field" for="ag-ordre">
							<span class="sci-field-label">Ordre du jour</span>
							<textarea
								id="ag-ordre"
								class="sci-textarea min-h-24"
								placeholder="Approbation des comptes, affectation du résultat, arbitrages..."
								bind:value={editor.ordre_du_jour}
							></textarea>
						</label>

						<label class="sci-field" for="ag-resolutions">
							<span class="sci-field-label">Résolutions</span>
							<textarea
								id="ag-resolutions"
								class="sci-textarea min-h-28"
								placeholder="Résolution 1 : approbation des comptes. Résolution 2 : distribution..."
								bind:value={editor.resolutions}
							></textarea>
						</label>

						<label class="sci-field" for="ag-notes">
							<span class="sci-field-label">Notes de séance</span>
							<textarea
								id="ag-notes"
								class="sci-textarea min-h-28"
								placeholder="Décisions prises, points de vigilance, actions de suivi..."
								bind:value={editor.notes}
							></textarea>
						</label>

						<label class="sci-field" for="ag-pv-url">
							<span class="sci-field-label">Lien de partage du procès-verbal</span>
							<input
								id="ag-pv-url"
								type="url"
								class="sci-input"
								placeholder="https://..."
								bind:value={editor.pv_url}
							/>
						</label>

						<div class="flex flex-wrap justify-end gap-2">
							<button
								type="button"
								class="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-900"
								onclick={closeEditor}
							>
								Annuler
							</button>
							<button
								type="button"
								class="rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
								disabled={saving}
								onclick={handleSave}
							>
								{saving ? 'Enregistrement...' : editingId ? 'Mettre à jour l’AG' : 'Créer l’AG'}
							</button>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
<!-- Convocation Modal -->
{#if showConvocationModal && convocationData}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true">
		<div class="mx-4 w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-950">
			<div class="flex items-center justify-between mb-4">
				<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Convocation</h3>
				<button
					onclick={() => { showConvocationModal = false; }}
					class="rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
				>
					<X class="h-5 w-5" />
				</button>
			</div>
			<div class="max-h-96 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
				<pre class="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-300">{convocationData.texte}</pre>
			</div>
			<div class="mt-4 flex justify-end gap-2">
				<button
					onclick={copyConvocation}
					class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-900"
				>
					<Copy class="h-4 w-4" />
					Copier
				</button>
				<button
					onclick={downloadConvocation}
					class="inline-flex items-center gap-2 rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700"
				>
					<Download class="h-4 w-4" />
					Télécharger
				</button>
			</div>
		</div>
	</div>
{/if}

</section>
