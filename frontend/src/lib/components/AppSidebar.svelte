<script lang="ts">
	import { page } from '$app/state';
	import {
		LayoutDashboard,
		Building2,
		HandCoins,
		FileText,
		Calculator,
		Settings,
		User,
		HelpCircle,
		ChevronsLeft,
		ChevronsRight
	} from 'lucide-svelte';
	import { sidebarCollapsed } from '$lib/stores/sidebar';
	import SidebarSCISwitcher from './SidebarSCISwitcher.svelte';

	interface Props {
		user: { email?: string } | null;
		scis?: Array<{ id: string | number; nom: string; statut?: string | null }>;
		activeSciId?: string;
		onSciChange?: (id: string) => void;
	}

	let { user, scis = [], activeSciId = '', onSciChange }: Props = $props();

	const navItems = [
		{ href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
		{ href: '/biens', label: 'Biens', icon: Building2 },
		{ href: '/loyers', label: 'Loyers', icon: HandCoins },
		{ href: '/documents', label: 'Documents', icon: FileText },
		{ href: '/fiscalite', label: 'Fiscalité', icon: Calculator }
	];

	const utilityItems = [
		{ href: '/settings', label: 'Paramètres', icon: Settings },
		{ href: '/account', label: 'Compte', icon: User },
		{ href: '/pricing', label: 'Tarifs', icon: HelpCircle }
	];

	function isActive(href: string) {
		return page.url.pathname === href || (href !== '/' && page.url.pathname.startsWith(`${href}/`));
	}
</script>

<aside
	class="hidden flex-shrink-0 border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-all duration-200 md:flex md:flex-col {$sidebarCollapsed ? 'w-16' : 'w-60'}"
>
	<div class="flex h-14 items-center justify-between border-b border-sidebar-border px-3">
		{#if !$sidebarCollapsed}
			<span class="text-sm font-bold tracking-tight">GererSCI</span>
		{/if}
		<button
			type="button"
			class="rounded-md p-1.5 text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
			onclick={() => sidebarCollapsed.toggle()}
			aria-label={$sidebarCollapsed ? 'Ouvrir la sidebar' : 'Réduire la sidebar'}
		>
			{#if $sidebarCollapsed}
				<ChevronsRight class="h-4 w-4" />
			{:else}
				<ChevronsLeft class="h-4 w-4" />
			{/if}
		</button>
	</div>

	{#if scis.length > 0}
		<div class="border-b border-sidebar-border px-3 py-3">
			<SidebarSCISwitcher
				{scis}
				{activeSciId}
				collapsed={$sidebarCollapsed}
				{onSciChange}
			/>
		</div>
	{/if}

	<nav class="flex-1 space-y-1 px-2 py-3">
		<p class="mb-2 px-2 text-[0.6rem] font-semibold tracking-[0.2em] text-sidebar-foreground/50 uppercase">
			{#if !$sidebarCollapsed}Pilotage{/if}
		</p>
		{#each navItems as item (item.href)}
			<a
				href={item.href}
				aria-current={isActive(item.href) ? 'page' : undefined}
				class="flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors {isActive(item.href)
					? 'bg-sidebar-primary text-sidebar-primary-foreground'
					: 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'}"
				title={$sidebarCollapsed ? item.label : undefined}
			>
				<item.icon class="h-4 w-4 flex-shrink-0" />
				{#if !$sidebarCollapsed}
					<span>{item.label}</span>
				{/if}
			</a>
		{/each}
	</nav>

	<div class="border-t border-sidebar-border px-2 py-3">
		<p class="mb-2 px-2 text-[0.6rem] font-semibold tracking-[0.2em] text-sidebar-foreground/50 uppercase">
			{#if !$sidebarCollapsed}Compte{/if}
		</p>
		{#each utilityItems as item (item.href)}
			<a
				href={item.href}
				aria-current={isActive(item.href) ? 'page' : undefined}
				class="flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors {isActive(item.href)
					? 'bg-sidebar-primary text-sidebar-primary-foreground'
					: 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'}"
				title={$sidebarCollapsed ? item.label : undefined}
			>
				<item.icon class="h-4 w-4 flex-shrink-0" />
				{#if !$sidebarCollapsed}
					<span>{item.label}</span>
				{/if}
			</a>
		{/each}
	</div>

	{#if user?.email && !$sidebarCollapsed}
		<div class="border-t border-sidebar-border px-3 py-3">
			<p class="truncate text-xs text-sidebar-foreground/50">{user.email}</p>
		</div>
	{/if}
</aside>
