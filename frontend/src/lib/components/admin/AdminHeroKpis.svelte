<script lang="ts">
	import {
		Target,
		Euro,
		Zap,
		UserMinus,
		ArrowUpRight,
		TrendingUp,
		TrendingDown,
		Minus,
		Info
	} from 'lucide-svelte';

	type MetricValue = {
		value: number;
		previous: number;
		trend: string;
		change_pct: number | null;
	};

	type Props = {
		metrics: {
			north_star: MetricValue;
			mrr: MetricValue;
			activation_rate: MetricValue;
			churn_30d: MetricValue;
			conversion_rate: MetricValue;
		};
	};

	let { metrics }: Props = $props();

	const kpis = $derived([
		{
			key: 'north_star',
			label: 'North Star',
			subtitle: 'SCIs actives sur 30j',
			tooltip:
				"Combien de SCI ont enregistré ≥1 loyer payé ces 30 derniers jours. C'est ta métrique #1 — si elle monte, ton produit crée de la valeur. Si elle stagne, concentre-toi sur l'activation.",
			icon: Target,
			color: 'indigo',
			format: 'integer',
			positiveUp: true,
			data: metrics.north_star
		},
		{
			key: 'mrr',
			label: 'MRR',
			subtitle: 'Revenu mensuel recurrent',
			tooltip:
				"Somme des abonnements actifs ce mois (hors lifetime). C'est ce qui paie tes serveurs. Surveille la tendance : 2 semaines de baisse = signal d'alerte.",
			icon: Euro,
			color: 'emerald',
			format: 'currency',
			positiveUp: true,
			data: metrics.mrr
		},
		{
			key: 'activation_rate',
			label: 'Activation',
			subtitle: 'Inscrits → 1er loyer',
			tooltip:
				"% d'utilisateurs inscrits qui ont enregistré au moins 1 loyer. En dessous de 30%, ton onboarding a un problème — simplifie le parcours.",
			icon: Zap,
			color: 'sky',
			format: 'percentage',
			positiveUp: true,
			data: metrics.activation_rate
		},
		{
			key: 'churn_30d',
			label: 'Churn 30j',
			subtitle: 'Users perdus ce mois',
			tooltip:
				"% d'utilisateurs actifs le mois dernier qui ne le sont plus ce mois-ci. Au-dessus de 5%/mois, il y a une fuite à colmater — contacte les users perdus.",
			icon: UserMinus,
			color: 'rose',
			format: 'percentage',
			positiveUp: false,
			data: metrics.churn_30d
		},
		{
			key: 'conversion_rate',
			label: 'Conversion',
			subtitle: 'Free vers payant',
			tooltip:
				"% d'utilisateurs gratuits passés à un plan payant. Bon indicateur de la valeur perçue et du positionnement de ton paywall.",
			icon: ArrowUpRight,
			color: 'amber',
			format: 'percentage',
			positiveUp: true,
			data: metrics.conversion_rate
		}
	]);

	function formatValue(value: number, format: string): string {
		if (format === 'currency') return `${value.toLocaleString('fr-FR')} €`;
		if (format === 'percentage') return `${value}%`;
		return String(Math.round(value));
	}

	const colorMap: Record<string, { bg: string; icon: string; darkBg: string }> = {
		indigo: { bg: 'bg-indigo-50', icon: 'text-indigo-500', darkBg: 'dark:bg-indigo-950/40' },
		emerald: { bg: 'bg-emerald-50', icon: 'text-emerald-500', darkBg: 'dark:bg-emerald-950/40' },
		sky: { bg: 'bg-sky-50', icon: 'text-sky-500', darkBg: 'dark:bg-sky-950/40' },
		rose: { bg: 'bg-rose-50', icon: 'text-rose-500', darkBg: 'dark:bg-rose-950/40' },
		amber: { bg: 'bg-amber-50', icon: 'text-amber-500', darkBg: 'dark:bg-amber-950/40' }
	};
</script>

<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
	{#each kpis as kpi (kpi.key)}
		{@const c = colorMap[kpi.color]}
		{@const trendGood = kpi.data.trend === 'up'}
		{@const trendBad = kpi.data.trend === 'down'}
		<div
			class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
		>
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2">
					<div class="flex h-8 w-8 items-center justify-center rounded-lg {c.bg} {c.darkBg}">
						<kpi.icon class="h-4 w-4 {c.icon}" />
					</div>
					<p class="text-xs font-semibold tracking-wider text-slate-500 uppercase">{kpi.label}</p>
				</div>
				<button class="group relative ml-1 inline-flex cursor-help" aria-label="Info">
					<Info class="h-3.5 w-3.5 text-slate-400" />
					<div
						class="pointer-events-none absolute right-0 bottom-full z-50 mb-2 w-64 rounded-lg border border-slate-200 bg-white p-3 text-xs leading-relaxed text-slate-600 opacity-0 shadow-lg transition-opacity group-hover:opacity-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
					>
						{kpi.tooltip}
					</div>
				</button>
			</div>

			<div class="mt-3 flex items-end justify-between">
				<p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
					{formatValue(kpi.data.value, kpi.format)}
				</p>
				{#if kpi.data.change_pct != null}
					<div
						class="flex items-center gap-0.5 text-xs font-semibold {trendGood
							? 'text-emerald-600'
							: trendBad
								? 'text-rose-600'
								: 'text-slate-400'}"
					>
						{#if trendGood}
							<TrendingUp class="h-3.5 w-3.5" />
						{:else if trendBad}
							<TrendingDown class="h-3.5 w-3.5" />
						{:else}
							<Minus class="h-3.5 w-3.5" />
						{/if}
						{Math.abs(kpi.data.change_pct)}%
					</div>
				{:else}
					<span class="text-xs text-slate-400">—</span>
				{/if}
			</div>

			<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{kpi.subtitle}</p>
		</div>
	{/each}
</div>
