const eurFormatter = new Intl.NumberFormat('fr-FR', {
	style: 'currency',
	currency: 'EUR',
	maximumFractionDigits: 0
});

const frDateFormatter = new Intl.DateTimeFormat('fr-FR', {
	year: 'numeric',
	month: 'short',
	day: 'numeric'
});

export function formatEur(value: number | null | undefined, fallback = 'N/A') {
	if (typeof value !== 'number' || Number.isNaN(value)) {
		return fallback;
	}

	return eurFormatter.format(value);
}

export function formatFrDate(value: string | null | undefined, fallback = 'Date inconnue') {
	if (!value) {
		return fallback;
	}

	const parsed = new Date(value);
	if (Number.isNaN(parsed.getTime())) {
		return value;
	}

	return frDateFormatter.format(parsed);
}
