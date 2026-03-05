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
	});

	it('keeps readable API messages and falls back when needed', () => {
		expect(
			formatApiErrorMessage(new Error('Le montant est obligatoire.'), 'Fallback technique')
		).toBe('Le montant est obligatoire.');

		expect(formatApiErrorMessage(new Error(''), 'Fallback technique')).toBe('Fallback technique');
		expect(formatApiErrorMessage('erreur', 'Fallback technique')).toBe('Fallback technique');
	});

	it('humanizes associate roles and charge types', () => {
		expect(mapAssociateRoleLabel('gerant')).toBe('Gérant');
		expect(mapAssociateRoleLabel('associe')).toBe('Associé');
		expect(mapAssociateRoleLabel('co_gerant')).toBe('Gérant');
		expect(mapAssociateRoleLabel(undefined)).toBe('Associé');
		expect(mapChargeTypeLabel('taxe_fonciere')).toBe('Taxe Fonciere');
		expect(mapChargeTypeLabel('travaux')).toBe('Travaux');
		expect(mapChargeTypeLabel(undefined)).toBe('Charge');
	});
});
