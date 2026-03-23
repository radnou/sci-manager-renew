<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { page } from '$app/state';
	import { adminKey } from '$lib/stores/admin-auth';
	import { ArrowLeft, Mail, Shield, UserX, Crown } from 'lucide-svelte';
	import AdminUserStatusBadge from '$lib/components/admin/AdminUserStatusBadge.svelte';

	const userId = $derived(page.params.userId);

	let userData = $state<any>(null);
	let loading = $state(true);
	let actionLoading = $state('');
	let actionMessage = $state('');

	// Email form
	let showEmailForm = $state(false);
	let emailSubject = $state('');
	let emailBody = $state('');

	// Plan change
	let showPlanForm = $state(false);
	let selectedPlan = $state('free');

	async function adminFetch<T>(path: string, options?: RequestInit): Promise<T> {
		const headers = new Headers(options?.headers);
		headers.set('X-Admin-Key', get(adminKey));
		const resp = await fetch(path, { ...options, headers });
		if (!resp.ok) throw new Error(`${resp.status}`);
		return resp.json();
	}

	async function loadUser() {
		try {
			userData = await adminFetch(`/api/v1/admin/users/${userId}`);
		} catch {
			actionMessage = 'Erreur lors du chargement';
		} finally {
			loading = false;
		}
	}

	onMount(loadUser);

	async function changePlan() {
		actionLoading = 'plan';
		actionMessage = '';
		try {
			await adminFetch(`/api/v1/admin/users/${userId}/plan`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ plan: selectedPlan })
			});
			actionMessage = `Plan change en "${selectedPlan}"`;
			showPlanForm = false;
			await loadUser();
		} catch {
			actionMessage = 'Erreur lors du changement de plan';
		} finally {
			actionLoading = '';
		}
	}

	async function sendEmail() {
		if (!emailSubject.trim() || !emailBody.trim()) return;
		actionLoading = 'email';
		actionMessage = '';
		try {
			await adminFetch(`/api/v1/admin/users/${userId}/email`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ subject: emailSubject, message: emailBody })
			});
			actionMessage = `Email envoye a ${userData?.user?.email}`;
			showEmailForm = false;
			emailSubject = '';
			emailBody = '';
		} catch {
			actionMessage = "Erreur lors de l'envoi";
		} finally {
			actionLoading = '';
		}
	}

	async function disableUser() {
		if (
			!confirm(`Desactiver le compte de ${userData?.user?.email} ? Cette action est irreversible.`)
		)
			return;
		actionLoading = 'disable';
		actionMessage = '';
		try {
			await adminFetch(`/api/v1/admin/users/${userId}`, { method: 'DELETE' });
			actionMessage = 'Compte desactive';
		} catch {
			actionMessage = 'Erreur lors de la desactivation';
		} finally {
			actionLoading = '';
		}
	}
</script>

<svelte:head>
	<title>User Detail | Admin | GérerSCI</title>
</svelte:head>

<a
	href="/admin/users"
	class="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
>
	<ArrowLeft class="h-4 w-4" />
	Retour aux utilisateurs
</a>

{#if loading}
	<div class="flex items-center justify-center py-20">
		<div
			class="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-600"
		></div>
	</div>
{:else if userData}
	<!-- User Header -->
	<div
		class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
	>
		<div class="flex items-start justify-between">
			<div>
				<h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
					{userData.user.email}
				</h2>
				<p class="mt-1 text-sm text-slate-500">
					ID: {userData.user.id}
				</p>
				<p class="text-sm text-slate-500">
					Inscrit le {new Date(userData.user.created_at).toLocaleDateString('fr-FR')}
				</p>
			</div>
			<div class="flex items-center gap-2">
				{#if userData.subscription}
					<span
						class="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
					>
						{userData.subscription.status}
					</span>
				{:else}
					<span
						class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400"
					>
						Free
					</span>
				{/if}
			</div>
		</div>
	</div>

	<!-- Stats Grid -->
	<div class="mt-4 grid grid-cols-3 gap-4">
		<div
			class="rounded-2xl border border-slate-200 bg-white p-5 text-center dark:border-slate-800 dark:bg-slate-950"
		>
			<p class="text-2xl font-bold text-slate-900 dark:text-slate-100">{userData.scis.length}</p>
			<p class="text-xs text-slate-500">SCIs</p>
		</div>
		<div
			class="rounded-2xl border border-slate-200 bg-white p-5 text-center dark:border-slate-800 dark:bg-slate-950"
		>
			<p class="text-2xl font-bold text-slate-900 dark:text-slate-100">{userData.biens.length}</p>
			<p class="text-xs text-slate-500">Biens</p>
		</div>
		<div
			class="rounded-2xl border border-slate-200 bg-white p-5 text-center dark:border-slate-800 dark:bg-slate-950"
		>
			<p class="text-2xl font-bold text-slate-900 dark:text-slate-100">{userData.loyers_count}</p>
			<p class="text-xs text-slate-500">Loyers</p>
		</div>
	</div>

	<!-- SCIs List -->
	{#if userData.scis.length > 0}
		<div
			class="mt-4 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
		>
			<h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">SCIs</h3>
			<div class="mt-3 space-y-2">
				{#each userData.scis as assoc}
					<div
						class="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-2 dark:bg-slate-900"
					>
						<div>
							<p class="text-sm font-medium text-slate-900 dark:text-slate-100">
								{assoc.sci?.nom ?? 'SCI'}
							</p>
							<p class="text-xs text-slate-500">
								{assoc.role} — {assoc.nb_parts ?? '?'} parts
							</p>
						</div>
						<span class="text-xs text-slate-400">{assoc.sci?.siren ?? ''}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Biens List -->
	{#if userData.biens.length > 0}
		<div
			class="mt-4 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
		>
			<h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Biens</h3>
			<div class="mt-3 space-y-2">
				{#each userData.biens as bien}
					<div class="rounded-lg bg-slate-50 px-4 py-2 dark:bg-slate-900">
						<p class="text-sm font-medium text-slate-900 dark:text-slate-100">
							{bien.adresse}
						</p>
						<p class="text-xs text-slate-500">{bien.ville}</p>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Action Message -->
	{#if actionMessage}
		<div
			class="mt-4 rounded-xl border border-sky-200 bg-sky-50 px-5 py-3 text-sm text-sky-700 dark:border-sky-800 dark:bg-sky-950/30 dark:text-sky-300"
		>
			{actionMessage}
		</div>
	{/if}

	<!-- Actions -->
	<div
		class="mt-4 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950"
	>
		<h3 class="text-sm font-semibold text-slate-900 dark:text-slate-100">Actions</h3>
		<div class="mt-4 flex flex-wrap gap-3">
			<button
				class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
				onclick={() => (showPlanForm = !showPlanForm)}
			>
				<Crown class="h-4 w-4" />
				Changer le plan
			</button>
			<button
				class="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
				onclick={() => (showEmailForm = !showEmailForm)}
			>
				<Mail class="h-4 w-4" />
				Envoyer un email
			</button>
			<button
				class="inline-flex items-center gap-2 rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50"
				disabled={actionLoading === 'disable'}
				onclick={disableUser}
			>
				<UserX class="h-4 w-4" />
				{actionLoading === 'disable' ? 'En cours...' : 'Desactiver le compte'}
			</button>
		</div>

		<!-- Plan Change Form -->
		{#if showPlanForm}
			<div
				class="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
			>
				<p class="text-sm font-medium text-slate-700 dark:text-slate-300">Nouveau plan :</p>
				<div class="mt-2 flex items-center gap-3">
					<select
						bind:value={selectedPlan}
						class="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
					>
						<option value="free">Free</option>
						<option value="starter">Starter</option>
						<option value="pro">Pro</option>
					</select>
					<button
						class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
						disabled={actionLoading === 'plan'}
						onclick={changePlan}
					>
						{actionLoading === 'plan' ? 'En cours...' : 'Appliquer'}
					</button>
					<button
						class="text-sm text-slate-500 hover:text-slate-700"
						onclick={() => (showPlanForm = false)}
					>
						Annuler
					</button>
				</div>
			</div>
		{/if}

		<!-- Email Form -->
		{#if showEmailForm}
			<div
				class="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900"
			>
				<div class="space-y-3">
					<div>
						<label
							for="email-subject"
							class="text-xs font-medium text-slate-600 dark:text-slate-400">Sujet</label
						>
						<input
							type="text"
							bind:value={emailSubject}
							id="email-subject"
							placeholder="Sujet de l'email..."
							class="mt-1 h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
						/>
					</div>
					<div>
						<label for="email-body" class="text-xs font-medium text-slate-600 dark:text-slate-400"
							>Message</label
						>
						<textarea
							bind:value={emailBody}
							id="email-body"
							placeholder="Contenu de l'email..."
							rows="4"
							class="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
						></textarea>
					</div>
					<div class="flex gap-3">
						<button
							class="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
							disabled={actionLoading === 'email' || !emailSubject.trim() || !emailBody.trim()}
							onclick={sendEmail}
						>
							{actionLoading === 'email' ? 'Envoi...' : 'Envoyer'}
						</button>
						<button
							class="text-sm text-slate-500 hover:text-slate-700"
							onclick={() => (showEmailForm = false)}
						>
							Annuler
						</button>
					</div>
				</div>
			</div>
		{/if}
	</div>
{/if}
