<script lang="ts">
	type Props = { status: string };
	let { status }: Props = $props();

	const config: Record<string, { label: string; classes: string }> = {
		power_user: {
			label: 'Power user',
			classes: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
		},
		prospect: {
			label: 'Prospect chaud',
			classes: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
		},
		at_risk: {
			label: 'A risque',
			classes: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400'
		},
		new: {
			label: 'Nouveau',
			classes: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400'
		},
		active: {
			label: 'Actif',
			classes: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
		}
	};

	const c = $derived(config[status] ?? config.active);
</script>

<span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold {c.classes}">
	{c.label}
</span>
