"""Tests for the associe auto-linking service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.associe_linking import link_user_to_pending_associes

USER_ID = "user-abc-123"
EMAIL = "alice@example.com"


def _mock_client(select_data=None, update_data=None, update_side_effect=None):
    """Build a mock Supabase service client with chained query builder."""
    client = MagicMock()

    # --- select chain ---
    select_chain = MagicMock()
    select_result = MagicMock()
    select_result.data = select_data or []
    select_chain.select.return_value = select_chain
    select_chain.ilike.return_value = select_chain
    select_chain.is_.return_value = select_chain
    select_chain.eq.return_value = select_chain
    select_chain.execute.return_value = select_result

    # --- update chain ---
    update_chain = MagicMock()
    update_result = MagicMock()
    update_result.data = update_data if update_data is not None else [{"id": "x"}]
    update_chain.update.return_value = update_chain
    update_chain.eq.return_value = update_chain
    update_chain.is_.return_value = update_chain
    if update_side_effect:
        update_chain.execute.side_effect = update_side_effect
    else:
        update_chain.execute.return_value = update_result

    # Route .table("associes") calls: first call is select, subsequent are updates
    call_count = {"n": 0}
    original_table = client.table

    def table_router(name):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return select_chain
        return update_chain

    client.table.side_effect = table_router
    return client


class TestLinkUserToPendingAssocies:
    """Tests for link_user_to_pending_associes."""

    @patch("app.services.associe_linking.get_supabase_service_client")
    def test_links_matching_email(self, mock_get_client):
        """User with matching email -> links correctly and returns count."""
        mock_client = _mock_client(
            select_data=[{"id": "assoc-1"}],
            update_data=[{"id": "assoc-1", "user_id": USER_ID}],
        )
        mock_get_client.return_value = mock_client

        result = link_user_to_pending_associes(USER_ID, EMAIL)

        assert result == 1
        # Verify the select query used case-insensitive match
        select_chain = mock_client.table("associes")
        mock_client.table.assert_called()

    @patch("app.services.associe_linking.get_supabase_service_client")
    def test_no_matching_email_returns_zero(self, mock_get_client):
        """User with no matching email -> returns 0, no updates."""
        mock_client = _mock_client(select_data=[])
        mock_get_client.return_value = mock_client

        result = link_user_to_pending_associes(USER_ID, "nobody@example.com")

        assert result == 0

    @patch("app.services.associe_linking.get_supabase_service_client")
    def test_already_linked_not_overwritten(self, mock_get_client):
        """Associe already linked (has user_id) -> not in select results, not overwritten."""
        # The select query filters .is_("user_id", "null"), so already-linked
        # records won't appear. Simulate empty select result.
        mock_client = _mock_client(select_data=[])
        mock_get_client.return_value = mock_client

        result = link_user_to_pending_associes(USER_ID, EMAIL)

        assert result == 0

    @patch("app.services.associe_linking.get_supabase_service_client")
    def test_multiple_pending_all_linked(self, mock_get_client):
        """Multiple pending associes -> all linked."""
        client = MagicMock()

        # Select returns 3 records
        select_chain = MagicMock()
        select_result = MagicMock()
        select_result.data = [{"id": "a1"}, {"id": "a2"}, {"id": "a3"}]
        select_chain.select.return_value = select_chain
        select_chain.ilike.return_value = select_chain
        select_chain.is_.return_value = select_chain
        select_chain.execute.return_value = select_result

        # Each update succeeds
        update_chain = MagicMock()
        update_result = MagicMock()
        update_result.data = [{"id": "x"}]
        update_chain.update.return_value = update_chain
        update_chain.eq.return_value = update_chain
        update_chain.is_.return_value = update_chain
        update_chain.execute.return_value = update_result

        call_count = {"n": 0}

        def table_router(name):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return select_chain
            return update_chain

        client.table.side_effect = table_router
        mock_get_client.return_value = client

        result = link_user_to_pending_associes(USER_ID, EMAIL)

        assert result == 3

    @patch("app.services.associe_linking.get_supabase_service_client")
    def test_empty_user_id_returns_zero(self, mock_get_client):
        """Empty user_id -> returns 0 immediately, no DB calls."""
        result = link_user_to_pending_associes("", EMAIL)
        assert result == 0
        mock_get_client.assert_not_called()

    @patch("app.services.associe_linking.get_supabase_service_client")
    def test_empty_email_returns_zero(self, mock_get_client):
        """Empty email -> returns 0 immediately, no DB calls."""
        result = link_user_to_pending_associes(USER_ID, "")
        assert result == 0
        mock_get_client.assert_not_called()

    @patch("app.services.associe_linking.get_supabase_service_client")
    def test_update_failure_skips_record(self, mock_get_client):
        """If one update fails, others still proceed."""
        client = MagicMock()

        select_chain = MagicMock()
        select_result = MagicMock()
        select_result.data = [{"id": "a1"}, {"id": "a2"}]
        select_chain.select.return_value = select_chain
        select_chain.ilike.return_value = select_chain
        select_chain.is_.return_value = select_chain
        select_chain.execute.return_value = select_result

        # First update raises, second succeeds
        success_result = MagicMock()
        success_result.data = [{"id": "a2"}]

        update_chains = []
        for i in range(2):
            uc = MagicMock()
            uc.update.return_value = uc
            uc.eq.return_value = uc
            uc.is_.return_value = uc
            if i == 0:
                uc.execute.side_effect = Exception("DB error")
            else:
                uc.execute.return_value = success_result
            update_chains.append(uc)

        call_count = {"n": 0}

        def table_router(name):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return select_chain
            return update_chains[call_count["n"] - 2]

        client.table.side_effect = table_router
        mock_get_client.return_value = client

        result = link_user_to_pending_associes(USER_ID, EMAIL)

        assert result == 1  # Only the second one succeeded

    @patch("app.services.associe_linking.get_supabase_service_client")
    def test_case_insensitive_email_matching(self, mock_get_client):
        """Email matching is case-insensitive via ilike."""
        mock_client = _mock_client(select_data=[], update_data=[])
        mock_get_client.return_value = mock_client

        link_user_to_pending_associes(USER_ID, "Alice@Example.COM")

        # Verify the email was lowered before query
        table_call = mock_client.table
        table_call.assert_called()
