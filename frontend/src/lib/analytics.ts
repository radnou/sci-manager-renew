/**
 * Umami analytics event tracking helper.
 * Wraps window.umami?.track() with type safety.
 */

declare global {
	interface Window {
		umami?: {
			track: (event: string, data?: Record<string, string | number | boolean>) => void;
		};
	}
}

export function trackEvent(event: string, data?: Record<string, string | number | boolean>): void {
	try {
		window.umami?.track(event, data);
	} catch {
		// Silent fail — analytics should never break the app
	}
}

// Pre-defined event names for consistency
export const EVENTS = {
	// Landing page
	LANDING_CTA_CLICK: 'landing_cta_click',
	LANDING_PLAN_SELECT: 'landing_plan_select',
	LANDING_STEP_MODAL_OPEN: 'landing_step_modal_open',
	LANDING_FAQ_OPEN: 'landing_faq_open',
	LANDING_LIGHTBOX_OPEN: 'landing_lightbox_open',

	// Auth
	LOGIN_START: 'login_start',
	LOGIN_SUCCESS: 'login_success',
	REGISTER_START: 'register_start',
	REGISTER_SUCCESS: 'register_success',
	LOGOUT: 'logout',

	// Demo
	DEMO_SEED_START: 'demo_seed_start',
	DEMO_SEED_COMPLETE: 'demo_seed_complete',
	DEMO_LOCKED_ACTION: 'demo_locked_action',
	DEMO_UPGRADE_PROMPT: 'demo_upgrade_prompt',
	DEMO_BANNER_CTA: 'demo_banner_cta',

	// Pricing / Checkout
	PRICING_VIEW: 'pricing_view',
	PRICING_PLAN_SELECT: 'pricing_plan_select',
	CHECKOUT_MODAL_OPEN: 'checkout_modal_open',
	CHECKOUT_CONSENT: 'checkout_consent',
	CHECKOUT_CONFIRM: 'checkout_confirm',
	BILLING_TOGGLE: 'billing_toggle',

	// Onboarding
	ONBOARDING_STEP: 'onboarding_step',
	ONBOARDING_COMPLETE: 'onboarding_complete',

	// App core actions
	SCI_CREATE: 'sci_create',
	BIEN_CREATE: 'bien_create',
	BIEN_EDIT: 'bien_edit',
	BAIL_CREATE: 'bail_create',
	LOYER_CREATE: 'loyer_create',
	LOYER_MARK_PAID: 'loyer_mark_paid',
	CHARGE_CREATE: 'charge_create',
	QUITTANCE_GENERATE: 'quittance_generate',
	QUITTANCE_EMAIL_SEND: 'quittance_email_send',
	DOCUMENT_UPLOAD: 'document_upload',
	EXPORT_CSV: 'export_csv',
	EXPORT_PDF: 'export_pdf',

	// Navigation
	THEME_TOGGLE: 'theme_toggle',
	SCI_SWITCH: 'sci_switch',
	TAB_SWITCH: 'tab_switch',

	// Simulateur
	SIMULATEUR_CERFA_CALCULATE: 'simulateur_cerfa_calculate',
	SIMULATEUR_EMAIL_CAPTURE: 'simulateur_email_capture',

	// Celebrations
	MILESTONE_FIRST_LOYER: 'milestone_first_loyer',
	MILESTONE_FIRST_QUITTANCE: 'milestone_first_quittance',
	MILESTONE_DASHBOARD_COMPLETE: 'milestone_dashboard_complete',
} as const;
