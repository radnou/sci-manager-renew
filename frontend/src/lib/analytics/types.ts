export type EventProps = Record<string, string | number | boolean>;

export interface AnalyticsProvider {
	readonly name: string;
	isConfigured(): boolean;
	init(): void;
	trackPageview(url?: string): void;
	trackEvent(event: string, props?: EventProps): void;
	/** Called when the user accepts analytics cookies. Optional. */
	grantConsent?(): void;
	/** Called when the user refuses or revokes consent. Optional. */
	revokeConsent?(): void;
}
