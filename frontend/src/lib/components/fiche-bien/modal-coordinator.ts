const FICHE_BIEN_MODAL_EVENT = 'fiche-bien-modal-change';

export function announceFicheBienModal(modalId: string | null) {
	if (typeof window === 'undefined') return;
	window.dispatchEvent(new CustomEvent<string | null>(FICHE_BIEN_MODAL_EVENT, { detail: modalId }));
}

export function subscribeExclusiveFicheBienModal(modalId: string, onClose: () => void) {
	if (typeof window === 'undefined') {
		return () => {};
	}

	const handler = (event: Event) => {
		const activeModalId = (event as CustomEvent<string | null>).detail;
		if (activeModalId !== modalId) {
			onClose();
		}
	};

	window.addEventListener(FICHE_BIEN_MODAL_EVENT, handler);
	return () => window.removeEventListener(FICHE_BIEN_MODAL_EVENT, handler);
}
