import { describe, expect, it } from 'vitest';
import { formatApiErrorMessage, mapAssociateRoleLabel, mapChargeTypeLabel } from './presentation';

describe('high-value presentation helpers', () => {
	it('formats known API auth and network errors into product messages', () => {
		expect(
			formatApiErrorMessage(new Error('{"detail":"Invalid bearer token"}'), 'Fallback technique')
		).toBe('Votre session est invalide ou expirée. Recharge la page ou reconnecte-toi.');

		expect(formatApiErrorMessage(new Error('Failed to fetch'), 'Fallback technique')).toBe(
			'Le service est indisponible pour le moment. Vérifie que le backend local est démarré puis recharge la page.'
		);

		expect(
			formatApiErrorMessage(
				new Error('{"error":"Le quota biens est atteint.","code":"plan_limit_reached","details":{"resource":"biens"}}'),
				'Fallback technique'
			)
		).toBe(
			"Le quota de biens de ton offre est atteint. Passe à une offre supérieure pour continuer."
		);
	});

	it('keeps readable API messages and falls back when needed', () => {
		expect(
			formatApiErrorMessage(new Error('Le montant est obligatoire.'), 'Fallback technique')
		).toBe('Le montant est obligatoire.');
		expect(
			formatApiErrorMessage(new Error('{"message":"Message structuré"}'), 'Fallback technique')
		).toBe('Message structuré');
		expect(
			formatApiErrorMessage(new Error('"Message JSON string"'), 'Fallback technique')
		).toBe('Message JSON string');

		expect(formatApiErrorMessage(new Error(''), 'Fallback technique')).toBe('Fallback technique');
		expect(formatApiErrorMessage('erreur', 'Fallback technique')).toBe('Fallback technique');
	});

	it('formats plan_limit_reached for scis quota and generic quota', () => {
		expect(
			formatApiErrorMessage(
				new Error('{"error":"Quota atteint","code":"plan_limit_reached","details":{"resource":"scis"}}'),
				'Fallback technique'
			)
		).toBe("Le quota de SCI de ton offre est atteint. Passe à une offre supérieure pour continuer.");

		expect(
			formatApiErrorMessage(
				new Error('{"error":"Quota atteint","code":"plan_limit_reached","details":{"resource":"other"}}'),
				'Fallback technique'
			)
		).toBe("Le quota de l'offre active est atteint.");

		expect(
			formatApiErrorMessage(
				new Error('{"error":"Quota atteint","code":"plan_limit_reached"}'),
				'Fallback technique'
			)
		).toBe("Le quota de l'offre active est atteint.");
	});

	it('formats upgrade_required errors with detail message', () => {
		expect(
			formatApiErrorMessage(
				new Error('{"detail":"Fonctionnalité Pro requise","code":"upgrade_required"}'),
				'Fallback technique'
			)
		).toBe('Fonctionnalité Pro requise');
	});

	it('formats upgrade_required errors with error field', () => {
		expect(
			formatApiErrorMessage(
				new Error('{"error":"Upgrade needed","code":"upgrade_required"}'),
				'Fallback technique'
			)
		).toBe('Upgrade needed');
	});

	it('formats subscription_inactive errors', () => {
		expect(
			formatApiErrorMessage(
				new Error('{"detail":"Abonnement inactif","code":"subscription_inactive"}'),
				'Fallback technique'
			)
		).toBe("L'abonnement actif ne permet pas cette opération. Vérifie ton offre ou réactive-la.");
	});

	it('passes through normalized message for unrecognized JSON objects', () => {
		expect(
			formatApiErrorMessage(
				new Error('{"code":"unknown","unexpected_field":true}'),
				'Fallback technique'
			)
		).toBe('{"code":"unknown","unexpected_field":true}');
	});

	it('returns fallback when structured error parses to empty JSON string', () => {
		expect(
			formatApiErrorMessage(
				new Error('""'),
				'Erreur vide'
			)
		).toBe('Erreur vide');
	});

	it('humanizes associate roles and charge types', () => {
		expect(mapAssociateRoleLabel('gerant')).toBe('Gérant');
		expect(mapAssociateRoleLabel('associe')).toBe('Associé');
		expect(mapAssociateRoleLabel('co_gerant')).toBe('Gérant');
		expect(mapAssociateRoleLabel('president_du_conseil')).toBe('President Du Conseil');
		expect(mapAssociateRoleLabel(undefined)).toBe('Associé');
		expect(mapChargeTypeLabel('taxe_fonciere')).toBe('Taxe Fonciere');
		expect(mapChargeTypeLabel('travaux')).toBe('Travaux');
		expect(mapChargeTypeLabel(undefined)).toBe('Charge');
	});

	it('preserves short digit-only tokens in toTitleCase via charge type mapping', () => {
		// normalizeMachineToken lowercases everything, but digits stay unchanged
		// A charge type "lot_42" produces tokens ["lot", "42"]
		// "42" has length <= 3 and "42" === "42".toUpperCase() => preserved as-is
		expect(mapChargeTypeLabel('lot_42')).toBe('Lot 42');
	});

	it('handles null role label', () => {
		expect(mapAssociateRoleLabel(null)).toBe('Associé');
	});

	it('handles null charge type label', () => {
		expect(mapChargeTypeLabel(null)).toBe('Charge');
	});

	it('handles empty string role', () => {
		expect(mapAssociateRoleLabel('')).toBe('Associé');
	});

	it('formats plan_limit_reached with null details gracefully', () => {
		expect(
			formatApiErrorMessage(
				new Error('{"detail":"Quota reached","code":"plan_limit_reached","details":null}'),
				'Fallback technique'
			)
		).toBe("Le quota de l'offre active est atteint.");
	});

	it('handles various network error patterns', () => {
		expect(
			formatApiErrorMessage(new Error('NetworkError when attempting to fetch resource'), 'Fallback')
		).toBe('Le service est indisponible pour le moment. Vérifie que le backend local est démarré puis recharge la page.');

		expect(
			formatApiErrorMessage(new Error('Load failed'), 'Fallback')
		).toBe('Le service est indisponible pour le moment. Vérifie que le backend local est démarré puis recharge la page.');

		expect(
			formatApiErrorMessage(new Error('Connection refused'), 'Fallback')
		).toBe('Le service est indisponible pour le moment. Vérifie que le backend local est démarré puis recharge la page.');
	});

	it('handles JWT and auth error patterns', () => {
		expect(
			formatApiErrorMessage(new Error('JWT expired'), 'Fallback')
		).toBe('Votre session est invalide ou expirée. Recharge la page ou reconnecte-toi.');

		expect(
			formatApiErrorMessage(new Error('Not authenticated'), 'Fallback')
		).toBe('Votre session est invalide ou expirée. Recharge la page ou reconnecte-toi.');

		expect(
			formatApiErrorMessage(new Error('Invalid token provided'), 'Fallback')
		).toBe('Votre session est invalide ou expirée. Recharge la page ou reconnecte-toi.');
	});
});
