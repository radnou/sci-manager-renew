<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
</script>

<svelte:head>
	<title>Politique de Confidentialité - GererSCI</title>
	<meta name="description" content="Politique de confidentialité et protection des données personnelles conforme au RGPD" />
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">
			Politique de Confidentialité
		</h1>
		<p class="text-slate-600 dark:text-slate-400">
			Dernière mise à jour : 5 mars 2026
		</p>
	</div>

	<div class="prose prose-slate dark:prose-invert max-w-none space-y-6">
		<!-- Section 1: Responsable du traitement -->
		<Card>
			<CardHeader>
				<CardTitle>1. Responsable du Traitement</CardTitle>
			</CardHeader>
			<CardContent class="space-y-3">
				<p><strong>GererSCI</strong></p>
				<p>Email : <a href="mailto:privacy@gerersci.fr" class="text-blue-600 dark:text-blue-400 hover:underline">privacy@gerersci.fr</a></p>
				<p>Site web : <a href="https://gerersci.fr" class="text-blue-600 dark:text-blue-400 hover:underline">https://gerersci.fr</a></p>
			</CardContent>
		</Card>

		<!-- Section 2: Données collectées -->
		<Card>
			<CardHeader>
				<CardTitle>2. Données Collectées</CardTitle>
			</CardHeader>
			<CardContent class="space-y-3">
				<h3 class="font-semibold text-slate-900 dark:text-slate-100">Données d'identification</h3>
				<ul class="list-disc list-inside space-y-1">
					<li>Email (obligatoire pour l'authentification)</li>
					<li>Adresse IP (collectée automatiquement)</li>
				</ul>

				<h3 class="font-semibold text-slate-900 dark:text-slate-100 mt-4">Données de gestion SCI</h3>
				<ul class="list-disc list-inside space-y-1">
					<li>Informations sur vos SCI (nom, SIRET)</li>
					<li>Données des biens immobiliers (adresse, type, loyers)</li>
					<li>Informations des associés (nom, parts sociales)</li>
					<li>Données locataires (nom, coordonnées, loyers)</li>
					<li>Données fiscales (revenus fonciers, charges)</li>
				</ul>

				<h3 class="font-semibold text-slate-900 dark:text-slate-100 mt-4">Données de paiement</h3>
				<p>Les données bancaires sont traitées directement par <strong>Stripe</strong>. Nous ne stockons pas vos informations de carte bancaire.</p>

				<h3 class="font-semibold text-slate-900 dark:text-slate-100 mt-4">Données techniques</h3>
				<ul class="list-disc list-inside space-y-1">
					<li>Cookies de session (authentification)</li>
					<li>Logs de connexion (IP, date, user-agent)</li>
				</ul>
			</CardContent>
		</Card>

		<!-- Section 3: Base légale -->
		<Card>
			<CardHeader>
				<CardTitle>3. Base Légale du Traitement</CardTitle>
			</CardHeader>
			<CardContent class="space-y-3">
				<ul class="list-disc list-inside space-y-2">
					<li><strong>Exécution du contrat</strong> : fourniture du service GererSCI (Art. 6.1.b RGPD)</li>
					<li><strong>Obligation légale</strong> : conservation des données fiscales et de facturation (Art. 6.1.c RGPD)</li>
					<li><strong>Consentement</strong> : cookies non-essentiels (Art. 6.1.a RGPD)</li>
				</ul>
			</CardContent>
		</Card>

		<!-- Section 4: Finalités -->
		<Card>
			<CardHeader>
				<CardTitle>4. Finalités du Traitement</CardTitle>
			</CardHeader>
			<CardContent class="space-y-2">
				<ul class="list-disc list-inside space-y-1">
					<li>Authentification et gestion de votre compte</li>
					<li>Fourniture du service de gestion SCI</li>
					<li>Génération de documents fiscaux (CERFA 2044, quittances)</li>
					<li>Traitement des paiements et facturation</li>
					<li>Support client et assistance technique</li>
					<li>Amélioration du service</li>
					<li>Respect des obligations légales (conservation fiscale)</li>
				</ul>
			</CardContent>
		</Card>

		<!-- Section 5: Durée de conservation -->
		<Card>
			<CardHeader>
				<CardTitle>5. Durée de Conservation</CardTitle>
			</CardHeader>
			<CardContent class="space-y-2">
				<ul class="list-disc list-inside space-y-1">
					<li><strong>Données de compte</strong> : durée de l'abonnement + 3 ans</li>
					<li><strong>Données fiscales</strong> : 10 ans (obligation légale - Code Général des Impôts)</li>
					<li><strong>Données de facturation</strong> : 10 ans (obligation comptable)</li>
					<li><strong>Logs de sécurité</strong> : 12 mois</li>
					<li><strong>Cookies de session</strong> : durée de la session</li>
				</ul>
			</CardContent>
		</Card>

		<!-- Section 6: Destinataires -->
		<Card>
			<CardHeader>
				<CardTitle>6. Destinataires des Données</CardTitle>
			</CardHeader>
			<CardContent class="space-y-3">
				<h3 class="font-semibold text-slate-900 dark:text-slate-100">Sous-traitants RGPD-conformes</h3>

				<div class="border-l-4 border-blue-500 pl-4 my-3">
					<p class="font-semibold">Stripe (Paiements)</p>
					<p class="text-sm text-slate-600 dark:text-slate-400">Traitement des paiements et abonnements</p>
					<p class="text-sm">Localisation : États-Unis (EU-US Data Privacy Framework + DPA)</p>
					<p class="text-sm">Certifications : PCI-DSS Level 1, SOC 2</p>
					<a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">
						Privacy Policy →
					</a>
				</div>

				<div class="border-l-4 border-green-500 pl-4 my-3">
					<p class="font-semibold">Supabase (Infrastructure)</p>
					<p class="text-sm text-slate-600 dark:text-slate-400">Hébergement base de données, authentification, stockage</p>
					<p class="text-sm">Localisation : Union Européenne (région eu-central-1)</p>
					<p class="text-sm">Certifications : SOC 2 Type 2, GDPR-compliant</p>
					<a href="https://supabase.com/privacy" target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">
						Privacy Policy →
					</a>
				</div>

				<div class="border-l-4 border-purple-500 pl-4 my-3">
					<p class="font-semibold">Resend (Emails)</p>
					<p class="text-sm text-slate-600 dark:text-slate-400">Emails transactionnels (magic links, notifications)</p>
					<p class="text-sm">Localisation : États-Unis (DPA disponible)</p>
					<a href="https://resend.com/privacy" target="_blank" rel="noopener noreferrer" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">
						Privacy Policy →
					</a>
				</div>
			</CardContent>
		</Card>

		<!-- Section 7: Transferts internationaux -->
		<Card>
			<CardHeader>
				<CardTitle>7. Transferts Hors Union Européenne</CardTitle>
			</CardHeader>
			<CardContent class="space-y-3">
				<p>Certains de nos sous-traitants sont situés aux États-Unis :</p>
				<ul class="list-disc list-inside space-y-2">
					<li><strong>Stripe Inc.</strong> : protégé par EU-US Data Privacy Framework + Standard Contractual Clauses (SCC)</li>
					<li><strong>Resend</strong> : Data Processing Agreement (DPA) signé avec garanties appropriées</li>
				</ul>
				<p class="mt-3 text-sm text-slate-600 dark:text-slate-400">
					Tous les transferts respectent les exigences de l'Art. 46 du RGPD avec garanties appropriées.
				</p>
			</CardContent>
		</Card>

		<!-- Section 8: Vos droits -->
		<Card>
			<CardHeader>
				<CardTitle>8. Vos Droits RGPD</CardTitle>
			</CardHeader>
			<CardContent class="space-y-3">
				<p>Conformément au RGPD, vous disposez des droits suivants :</p>
				<ul class="list-disc list-inside space-y-2">
					<li><strong>Droit d'accès</strong> (Art. 15) : obtenir une copie de vos données</li>
					<li><strong>Droit de rectification</strong> (Art. 16) : corriger vos données inexactes</li>
					<li><strong>Droit à l'effacement</strong> (Art. 17) : supprimer vos données ("droit à l'oubli")</li>
					<li><strong>Droit à la portabilité</strong> (Art. 20) : récupérer vos données dans un format structuré</li>
					<li><strong>Droit d'opposition</strong> (Art. 21) : vous opposer au traitement</li>
					<li><strong>Droit à la limitation</strong> (Art. 18) : limiter le traitement</li>
				</ul>

				<div class="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg mt-4">
					<p class="font-semibold mb-2">Exercer vos droits</p>
					<p class="text-sm mb-3">Accédez à votre espace "Mes données" pour exporter ou supprimer vos données.</p>
					<a href="/account/privacy">
						<Button variant="outline" size="sm">Gérer mes données →</Button>
					</a>
				</div>

				<p class="text-sm text-slate-600 dark:text-slate-400 mt-3">
					<strong>Contact</strong> : <a href="mailto:privacy@gerersci.fr" class="text-blue-600 dark:text-blue-400 hover:underline">privacy@gerersci.fr</a><br />
					<strong>Délai de réponse</strong> : 1 mois maximum (Art. 12.3 RGPD)
				</p>
			</CardContent>
		</Card>

		<!-- Section 9: Réclamation CNIL -->
		<Card>
			<CardHeader>
				<CardTitle>9. Droit de Réclamation</CardTitle>
			</CardHeader>
			<CardContent class="space-y-2">
				<p>Si vous estimez que vos droits ne sont pas respectés, vous pouvez introduire une réclamation auprès de la CNIL :</p>
				<p class="font-semibold mt-2">Commission Nationale de l'Informatique et des Libertés (CNIL)</p>
				<p class="text-sm">3 Place de Fontenoy - TSA 80715 - 75334 PARIS CEDEX 07</p>
				<p class="text-sm">
					Site web : <a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer" class="text-blue-600 dark:text-blue-400 hover:underline">
						www.cnil.fr
					</a>
				</p>
			</CardContent>
		</Card>

		<!-- Section 10: Cookies -->
		<Card>
			<CardHeader>
				<CardTitle>10. Politique de Cookies</CardTitle>
			</CardHeader>
			<CardContent class="space-y-3">
				<h3 class="font-semibold text-slate-900 dark:text-slate-100">Cookies essentiels (toujours actifs)</h3>
				<ul class="list-disc list-inside space-y-1">
					<li><code class="text-sm bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">sb-access-token</code> : JWT d'authentification Supabase</li>
					<li><code class="text-sm bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">sb-refresh-token</code> : Token de rafraîchissement</li>
					<li><code class="text-sm bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">theme</code> : Préférence dark/light mode</li>
				</ul>

				<h3 class="font-semibold text-slate-900 dark:text-slate-100 mt-4">Cookies non-essentiels</h3>
				<p class="text-slate-600 dark:text-slate-400">
					<strong>GererSCI n'utilise AUCUN cookie de tracking, analytics ou publicitaire.</strong>
				</p>
				<p class="text-sm">
					Nous ne partageons vos données avec aucun service de : Google Analytics, Facebook Pixel, réseaux sociaux, ou tracking comportemental.
				</p>
			</CardContent>
		</Card>

		<!-- Section 11: Sécurité -->
		<Card>
			<CardHeader>
				<CardTitle>11. Sécurité des Données</CardTitle>
			</CardHeader>
			<CardContent class="space-y-2">
				<p>Nous mettons en œuvre les mesures techniques et organisationnelles suivantes :</p>
				<ul class="list-disc list-inside space-y-1">
					<li>Chiffrement HTTPS (TLS 1.3) pour toutes les communications</li>
					<li>Chiffrement des données au repos (AES-256)</li>
					<li>Authentification sécurisée via magic link (pas de mots de passe stockés)</li>
					<li>Row Level Security (RLS) sur la base de données</li>
					<li>Logs d'audit pour traçabilité</li>
					<li>Sauvegardes automatiques quotidiennes</li>
					<li>Tests de sécurité réguliers</li>
				</ul>
			</CardContent>
		</Card>

		<!-- Section 12: Modifications -->
		<Card>
			<CardHeader>
				<CardTitle>12. Modifications de la Politique</CardTitle>
			</CardHeader>
			<CardContent>
				<p>
					Cette politique de confidentialité peut être mise à jour. Nous vous informerons de toute modification
					substantielle par email et via un bandeau sur l'application.
				</p>
				<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
					Date de dernière modification : 5 mars 2026
				</p>
			</CardContent>
		</Card>

		<!-- Contact -->
		<div class="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 p-6 rounded-lg mt-8">
			<h3 class="font-semibold text-lg mb-3">Des questions sur vos données ?</h3>
			<p class="text-sm mb-4">Notre équipe est à votre disposition pour toute question relative à la protection de vos données personnelles.</p>
			<a href="mailto:privacy@gerersci.fr">
				<Button>Contacter le service RGPD</Button>
			</a>
		</div>
	</div>
</div>
