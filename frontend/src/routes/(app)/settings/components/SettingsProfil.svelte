<script lang="ts">
	import type { User } from '@supabase/supabase-js';
	import { supabase } from '$lib/supabase';
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { addToast } from '$lib/components/ui/toast';

	interface Props {
		user: User | null;
		email: string;
	}

	let { user, email }: Props = $props();

	let newPassword = $state('');
	let newPasswordConfirm = $state('');
	let passwordLoading = $state(false);
	let passwordError = $state('');
	let passwordSuccess = $state(false);
	const passwordMinLength = 8;

	async function handlePasswordChange() {
		passwordError = '';
		passwordSuccess = false;

		if (newPassword !== newPasswordConfirm) {
			passwordError = 'Les mots de passe ne correspondent pas.';
			return;
		}

		if (newPassword.length < passwordMinLength) {
			passwordError = `Le mot de passe doit contenir au moins ${passwordMinLength} caractères.`;
			return;
		}

		passwordLoading = true;

		try {
			const { error } = await supabase.auth.updateUser({ password: newPassword });

			if (error) {
				passwordError = 'Erreur lors de la mise à jour du mot de passe.';
			} else {
				passwordSuccess = true;
				newPassword = '';
				newPasswordConfirm = '';
				addToast({
					title: 'Mot de passe mis à jour',
					description: 'Votre mot de passe a été modifié avec succès.',
					variant: 'success'
				});
			}
		} catch {
			passwordError = 'Erreur lors de la mise à jour du mot de passe.';
		} finally {
			passwordLoading = false;
		}
	}
</script>

<div id="panel-profil" role="tabpanel" aria-labelledby="tab-profil" class="space-y-6">
	<!-- Identity -->
	<Card class="sci-section-card">
		<CardHeader>
			<div>
				<CardTitle class="text-lg">Identité</CardTitle>
				<CardDescription>Adresse email de connexion et mode d'accès.</CardDescription>
			</div>
		</CardHeader>
		<CardContent class="grid gap-4 pt-0 sm:grid-cols-2">
			<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
				<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Email</p>
				<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">{email}</p>
			</div>
			<div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
				<p class="text-xs font-semibold tracking-[0.15em] uppercase text-slate-500">Mode d'accès</p>
				<p class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
					{user?.email ? 'Connexion par lien sécurisé' : 'Aucune session active'}
				</p>
			</div>
		</CardContent>
	</Card>

	<!-- Password change -->
	<Card class="sci-section-card">
		<CardHeader>
			<div>
				<CardTitle class="text-lg">Sécurité</CardTitle>
				<CardDescription>Modifiez votre mot de passe pour sécuriser votre compte.</CardDescription>
			</div>
		</CardHeader>
		<CardContent class="pt-0">
			<form class="max-w-md space-y-4" onsubmit={(e) => { e.preventDefault(); handlePasswordChange(); }}>
				<label class="sci-field">
					<span class="sci-field-label">Nouveau mot de passe</span>
					<Input
						type="password"
						bind:value={newPassword}
						placeholder="••••••••"
						disabled={passwordLoading}
						autocomplete="new-password"
					/>
				</label>
				<label class="sci-field">
					<span class="sci-field-label">Confirmer le nouveau mot de passe</span>
					<Input
						type="password"
						bind:value={newPasswordConfirm}
						placeholder="••••••••"
						disabled={passwordLoading}
						autocomplete="new-password"
					/>
				</label>

				{#if passwordError}
					<p class="sci-inline-alert sci-inline-alert-error">{passwordError}</p>
				{/if}

				{#if passwordSuccess}
					<p class="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
						Mot de passe mis à jour avec succès.
					</p>
				{/if}

				<Button
					type="submit"
					disabled={passwordLoading || !newPassword || !newPasswordConfirm || newPassword !== newPasswordConfirm || newPassword.length < passwordMinLength}
				>
					{passwordLoading ? 'Mise à jour...' : 'Modifier le mot de passe'}
				</Button>
			</form>
		</CardContent>
	</Card>
</div>
