export function formatApiErrorMessage(error: unknown, fallback: string) {
	if (!(error instanceof Error)) {
		return fallback;
	}

	const rawMessage = error.message.trim();
	if (!rawMessage) {
		return fallback;
	}

	const parsedError = parseStructuredErrorMessage(rawMessage);
	const parsedMessage = parsedError.message;
	if (!parsedMessage) {
		return fallback;
	}

	if (parsedError.code === 'plan_limit_reached') {
		const resource = String((parsedError.details as { resource?: string } | null)?.resource || '');
		if (resource === 'biens') {
			return 'Le quota de biens de ton offre est atteint. Passe à une offre supérieure pour continuer.';
		}
		if (resource === 'scis') {
			return 'Le quota de SCI de ton offre est atteint. Passe à une offre supérieure pour continuer.';
		}
		return "Le quota de l'offre active est atteint.";
	}

	if (parsedError.code === 'upgrade_required') {
		return parsedMessage || "Cette fonctionnalité nécessite une offre supérieure.";
	}

	if (parsedError.code === 'subscription_inactive') {
		return "L'abonnement actif ne permet pas cette opération. Vérifie ton offre ou réactive-la.";
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
			return { message: parsed.trim() || null, code: null, details: null };
		}

		if (parsed && typeof parsed === 'object') {
			const code = typeof parsed.code === 'string' ? parsed.code.trim() : null;
			const details = parsed.details ?? null;
			if (typeof parsed.detail === 'string' && parsed.detail.trim()) {
				return { message: parsed.detail.trim(), code, details };
			}

			if (typeof parsed.message === 'string' && parsed.message.trim()) {
				return { message: parsed.message.trim(), code, details };
			}

			if (typeof parsed.error === 'string' && parsed.error.trim()) {
				return { message: parsed.error.trim(), code, details };
			}
		}
	} catch {
		return { message: normalizedMessage, code: null, details: null };
	}

	return { message: normalizedMessage, code: null, details: null };
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
