"""Tests for admin metrics service."""

import pytest

from app.services.admin_metrics_service import _compute_trend


class TestComputeTrend:
    def test_trend_up(self):
        result = _compute_trend(current=30, previous=20, higher_is_better=True)
        assert result.value == 30
        assert result.previous == 20
        assert result.trend.value == "up"
        assert result.change_pct == pytest.approx(50.0)

    def test_trend_down(self):
        result = _compute_trend(current=10, previous=20, higher_is_better=True)
        assert result.trend.value == "down"
        assert result.change_pct == pytest.approx(-50.0)

    def test_trend_stable(self):
        result = _compute_trend(current=20, previous=20, higher_is_better=True)
        assert result.trend.value == "stable"
        assert result.change_pct == pytest.approx(0.0)

    def test_previous_zero_returns_none_change_pct(self):
        result = _compute_trend(current=5, previous=0, higher_is_better=True)
        assert result.change_pct is None
        assert result.trend.value == "up"

    def test_both_zero(self):
        result = _compute_trend(current=0, previous=0, higher_is_better=True)
        assert result.trend.value == "stable"
        assert result.change_pct is None

    def test_churn_lower_is_better(self):
        """For churn, a decrease is 'up' (good)."""
        result = _compute_trend(current=3, previous=5, higher_is_better=False)
        assert result.trend.value == "up"  # good direction

    def test_churn_increase_is_down(self):
        result = _compute_trend(current=7, previous=5, higher_is_better=False)
        assert result.trend.value == "down"  # bad direction

    def test_rounding(self):
        result = _compute_trend(current=33.333, previous=25.555, higher_is_better=True)
        assert result.value == 33.3
        assert result.previous == 25.6
