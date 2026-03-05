export function formatApiErrorMessage(error: unknown, fallback: string) {
	if (!(error instanceof Error)) {
		return fallback;
	}

	const rawMessage = error.message.trim();
	if (!rawMessage) {
		return fallback;
	}

	const parsedMessage = parseStructuredErrorMessage(rawMessage);
	if (!parsedMessage) {
		return fallback;
	}

	const normalizedMachineMessage = normalizeMachineToken(parsedMessage);
	if (
		normalizedMachineMessage.includes('invalid bearer token') ||
		normalizedMachineMessage.includes('invalid token') ||
		normalizedMachineMessage.includes('jwt') ||
		normalizedMachineMessage.includes('not authenticated')
	) {
		return 'Votre session est invalide ou expirée. Recharge la page ou reconnecte-toi.';
	}

	if (
		normalizedMachineMessage.includes('failed to fetch') ||
		normalizedMachineMessage.includes('networkerror') ||
		normalizedMachineMessage.includes('load failed') ||
		normalizedMachineMessage.includes('connection refused')
	) {
		return 'Le service est indisponible pour le moment. Vérifie que le backend local est démarré puis recharge la page.';
	}

	return parsedMessage;
}

export function mapAssociateRoleLabel(role: string | null | undefined) {
	const normalizedRole = normalizeMachineToken(role);
	if (!normalizedRole) {
		return 'Associé';
	}

	if (normalizedRole.includes('gerant')) {
		return 'Gérant';
	}

	if (normalizedRole.includes('associe')) {
		return 'Associé';
	}

	return toTitleCase(normalizedRole.replace(/_/g, ' '));
}

export function mapChargeTypeLabel(type: string | null | undefined) {
	const normalizedType = normalizeMachineToken(type);
	if (!normalizedType) {
		return 'Charge';
	}

	return toTitleCase(normalizedType.replace(/_/g, ' '));
}

function parseStructuredErrorMessage(rawMessage: string) {
	const normalizedMessage = rawMessage.replace(/\s+/g, ' ').trim();

	try {
		const parsed = JSON.parse(normalizedMessage);
		if (typeof parsed === 'string') {
			return parsed.trim() || null;
		}

		if (parsed && typeof parsed === 'object') {
			if (typeof parsed.detail === 'string' && parsed.detail.trim()) {
				return parsed.detail.trim();
			}

			if (typeof parsed.message === 'string' && parsed.message.trim()) {
				return parsed.message.trim();
			}
		}
	} catch {
		return normalizedMessage;
	}

	return normalizedMessage;
}

function normalizeMachineToken(value: string | null | undefined) {
	return (value || '')
		.trim()
		.toLowerCase()
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '');
}

function toTitleCase(value: string) {
	return value.replace(/\b\w+/g, (token) => {
		if (token.length <= 3 && token === token.toUpperCase()) {
			return token;
		}

		return token.charAt(0).toUpperCase() + token.slice(1);
	});
}
