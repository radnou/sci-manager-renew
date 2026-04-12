<script lang="ts">
	import { onMount } from 'svelte';
	import { driver, type DriveStep } from 'driver.js';
	import 'driver.js/dist/driver.css';

	const STORAGE_KEY = 'gerersci_product_tour_done';

	interface Props {
		/** Force-show the tour even if already completed */
		force?: boolean;
	}

	let { force = false }: Props = $props();

	const steps: DriveStep[] = [
		{
			element: '[data-tour="dashboard-kpis"]',
			popover: {
				title: 'Tableau de bord',
				description:
					'Vue consolidée de vos KPIs : revenus, charges, cashflow, taux de recouvrement. Tout se met à jour en temps réel.',
				side: 'bottom',
				align: 'center'
			}
		},
		{
			element: '[data-tour="nav-scis"]',
			popover: {
				title: 'Mes SCI',
				description:
					'Accédez à chaque SCI et ses biens. Chaque bien a 10 onglets : bail, loyers, charges, assurance, rentabilité...',
				side: 'bottom',
				align: 'start'
			}
		},
		{
			element: '[data-tour="nav-finances"]',
			popover: {
				title: 'Finances',
				description:
					'Vue financière consolidée sur toutes vos SCI : revenus, charges, cashflow net, évolution mensuelle.',
				side: 'bottom',
				align: 'start'
			}
		},
		{
			element: '[data-tour="nav-pilotage"]',
			popover: {
				title: 'Pilotage',
				description:
					'Bilans mensuels, échéances (baux, PNO, AG, déclarations), exploitation du parc immobilier.',
				side: 'bottom',
				align: 'start'
			}
		},
		{
			element: '[aria-label="Notifications"]',
			popover: {
				title: 'Notifications',
				description:
					'Alertes en temps réel : loyers impayés, baux expirants, quittances en attente, assurances PNO...',
				side: 'bottom',
				align: 'end'
			}
		},
		{
			element: '[data-tour="alerts"]',
			popover: {
				title: 'Alertes dashboard',
				description:
					'Les actions urgentes apparaissent ici : loyers en retard, baux à renouveler, documents manquants.',
				side: 'top',
				align: 'center'
			}
		}
	];

	function markDone() {
		try {
			localStorage.setItem(STORAGE_KEY, 'true');
		} catch {
			/* noop */
		}
	}

	export function start() {
		runTour();
	}

	function runTour() {
		const filteredSteps = steps.filter((step) => {
			if (!step.element) return true;
			return !!document.querySelector(step.element as string);
		});

		const driverObj = driver({
			showProgress: true,
			animate: true,
			smoothScroll: true,
			allowClose: true,
			overlayColor: 'rgba(0, 0, 0, 0.6)',
			stagePadding: 8,
			stageRadius: 12,
			popoverClass: 'gerersci-tour-popover',
			nextBtnText: 'Suivant',
			prevBtnText: 'Précédent',
			doneBtnText: 'Terminer',
			progressText: '{{current}} / {{total}}',
			steps: filteredSteps,
			onDestroyStarted: () => {
				markDone();
			},
			onDestroyed: () => {
				markDone();
			},
			onNextClick: (_el, step) => {
				const isLast = filteredSteps.indexOf(step) === filteredSteps.length - 1;
				if (isLast) {
					markDone();
				}
				driverObj.moveNext();
			},
			onCloseClick: () => {
				markDone();
				driverObj.destroy();
			}
		});
		driverObj.drive();
	}

	onMount(() => {
		if (force) {
			// Small delay to ensure DOM is fully rendered
			setTimeout(runTour, 800);
			return;
		}

		try {
			if (localStorage.getItem(STORAGE_KEY) !== 'true') {
				// First time: wait for dashboard to render, then start
				setTimeout(runTour, 1500);
			}
		} catch {
			/* localStorage unavailable */
		}
	});
</script>

<style>
	/* Override driver.js default styles for dark mode and brand consistency */
	:global(.gerersci-tour-popover) {
		font-family: inherit !important;
		border-radius: 1rem !important;
		box-shadow: 0 20px 60px -12px rgba(0, 0, 0, 0.25) !important;
	}

	:global(.gerersci-tour-popover .driver-popover-title) {
		font-size: 1rem !important;
		font-weight: 700 !important;
	}

	:global(.gerersci-tour-popover .driver-popover-description) {
		font-size: 0.875rem !important;
		color: #64748b !important;
		line-height: 1.5 !important;
	}

	:global(.gerersci-tour-popover .driver-popover-progress-text) {
		font-size: 0.75rem !important;
		color: #94a3b8 !important;
	}

	:global(.gerersci-tour-popover .driver-popover-next-btn),
	:global(.gerersci-tour-popover .driver-popover-done-btn) {
		background: #0284c7 !important;
		border-radius: 0.5rem !important;
		font-weight: 600 !important;
		padding: 0.375rem 0.75rem !important;
		font-size: 0.8125rem !important;
	}

	:global(.gerersci-tour-popover .driver-popover-prev-btn) {
		border-radius: 0.5rem !important;
		font-weight: 500 !important;
		padding: 0.375rem 0.75rem !important;
		font-size: 0.8125rem !important;
		color: #64748b !important;
	}

	/* Dark mode support */
	:global(.dark .gerersci-tour-popover) {
		background-color: #0f172a !important;
		border: 1px solid #334155 !important;
	}

	:global(.dark .gerersci-tour-popover .driver-popover-title) {
		color: #f1f5f9 !important;
	}

	:global(.dark .gerersci-tour-popover .driver-popover-description) {
		color: #94a3b8 !important;
	}

	:global(.dark .gerersci-tour-popover .driver-popover-close-btn) {
		color: #94a3b8 !important;
	}
</style>
