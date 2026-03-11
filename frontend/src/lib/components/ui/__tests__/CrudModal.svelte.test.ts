import { page } from 'vitest/browser';
import { describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import CrudModal from '../CrudModal.svelte';

describe('CrudModal', () => {
	it('renders nothing when open=false', async () => {
		render(CrudModal, {
			props: { open: false, title: 'Test', submitLabel: 'Save', loading: false }
		});
		await expect.element(page.getByRole('dialog')).not.toBeInTheDocument();
	});

	it('renders dialog with title and buttons when open=true', async () => {
		render(CrudModal, {
			props: { open: true, title: 'Test Modal', submitLabel: 'Enregistrer', loading: false }
		});
		await expect.element(page.getByRole('dialog')).toBeInTheDocument();
		await expect.element(page.getByText('Test Modal')).toBeInTheDocument();
		await expect.element(page.getByText('Enregistrer')).toBeInTheDocument();
		await expect.element(page.getByText('Annuler')).toBeInTheDocument();
	});

	it('shows subtitle when provided', async () => {
		render(CrudModal, {
			props: { open: true, title: 'T', subtitle: 'Sub text', submitLabel: 'OK', loading: false }
		});
		await expect.element(page.getByText('Sub text')).toBeInTheDocument();
	});

	it('disables submit button when loading', async () => {
		render(CrudModal, {
			props: { open: true, title: 'T', submitLabel: 'Save', loading: true }
		});
		const btn = page.getByRole('button', { name: /Chargement/ });
		await expect.element(btn).toBeDisabled();
	});

	it('has correct aria attributes', async () => {
		render(CrudModal, {
			props: { open: true, title: 'Accessible', submitLabel: 'OK', loading: false }
		});
		const dialog = page.getByRole('dialog');
		await expect.element(dialog).toHaveAttribute('aria-modal', 'true');
		await expect.element(dialog).toHaveAttribute('aria-labelledby');
	});
});
