import { page } from 'vitest/browser';
import { describe, expect, it, vi } from 'vitest';
import { render } from 'vitest-browser-svelte';
import LoyerModal from '../LoyerModal.svelte';
import ChargeModal from '../ChargeModal.svelte';
import SciModal from '../SciModal.svelte';
import AssocieModal from '../AssocieModal.svelte';

vi.mock('$lib/api', () => ({
	createLoyerForBien: vi.fn(),
	createChargeForBien: vi.fn(),
	createSci: vi.fn(),
	inviteAssocie: vi.fn()
}));

vi.mock('$lib/components/ui/toast/toast-store', () => ({
	addToast: vi.fn()
}));

vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

const noop = () => {};

describe('LoyerModal', () => {
	it('renders nothing when closed', async () => {
		render(LoyerModal, {
			props: { open: false, sciId: 'sci-1', bienId: 'bien-1', onSuccess: noop }
		});
		await expect.element(page.getByRole('dialog')).not.toBeInTheDocument();
	});

	it('shows form with title when open', async () => {
		render(LoyerModal, {
			props: { open: true, sciId: 'sci-1', bienId: 'bien-1', onSuccess: noop }
		});
		await expect.element(page.getByRole('dialog')).toBeInTheDocument();
		await expect.element(page.getByText('Enregistrer un loyer')).toBeInTheDocument();
	});
});

describe('ChargeModal', () => {
	it('renders nothing when closed', async () => {
		render(ChargeModal, {
			props: { open: false, sciId: 'sci-1', bienId: 'bien-1', onSuccess: noop }
		});
		await expect.element(page.getByRole('dialog')).not.toBeInTheDocument();
	});

	it('shows form with charge type selector when open', async () => {
		render(ChargeModal, {
			props: { open: true, sciId: 'sci-1', bienId: 'bien-1', onSuccess: noop }
		});
		await expect.element(page.getByRole('dialog')).toBeInTheDocument();
		await expect.element(page.getByText('Type de charge')).toBeInTheDocument();
	});
});

describe('SciModal', () => {
	it('renders nothing when closed', async () => {
		render(SciModal, {
			props: { open: false }
		});
		await expect.element(page.getByRole('dialog')).not.toBeInTheDocument();
	});

	it('shows form with title and SIREN field when open', async () => {
		render(SciModal, {
			props: { open: true }
		});
		await expect.element(page.getByRole('dialog')).toBeInTheDocument();
		await expect.element(page.getByText('Créer une SCI')).toBeInTheDocument();
		await expect.element(page.getByText('SIREN (optionnel)')).toBeInTheDocument();
	});
});

describe('AssocieModal', () => {
	it('renders nothing when closed', async () => {
		render(AssocieModal, {
			props: { open: false, sciId: 'sci-1', onSuccess: noop }
		});
		await expect.element(page.getByRole('dialog')).not.toBeInTheDocument();
	});

	it('shows form with title and role selector when open', async () => {
		render(AssocieModal, {
			props: { open: true, sciId: 'sci-1', onSuccess: noop }
		});
		await expect.element(page.getByRole('dialog')).toBeInTheDocument();
		await expect.element(page.getByText(/Inviter un associ/)).toBeInTheDocument();
		await expect.element(page.getByText('Associé')).toBeInTheDocument();
	});
});
