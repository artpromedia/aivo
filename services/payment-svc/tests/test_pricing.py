"""
Tests for pricing service functionality.
"""

from decimal import Decimal

from app.models import PlanType
from app.schemas import BASE_MONTHLY_PRICE, PLAN_DISCOUNTS, SIBLING_DISCOUNT


class TestPricingService:
    """Test pricing calculations."""

    def test_monthly_plan_no_discount(self, pricing_service):
        """Test monthly plan pricing without discounts."""
        result = pricing_service.calculate_pricing(
            plan_type=PlanType.MONTHLY, seats=5, has_sibling_discount=False
        )

        expected_base = BASE_MONTHLY_PRICE * 5 * 1  # 5 seats, 1 month

        assert result.base_amount == expected_base
        assert result.plan_discount_percentage == Decimal("0")
        assert result.plan_discount_amount == Decimal("0")
        assert result.sibling_discount_percentage == Decimal("0")
        assert result.sibling_discount_amount == Decimal("0")
        assert result.final_amount == expected_base
        assert result.seats == 5
        assert result.plan_type == PlanType.MONTHLY

    def test_quarterly_plan_with_discount(self, pricing_service):
        """Test quarterly plan with plan discount."""
        result = pricing_service.calculate_pricing(
            plan_type=PlanType.QUARTERLY, seats=3, has_sibling_discount=False
        )

        expected_base = BASE_MONTHLY_PRICE * 3 * 3  # 3 seats, 3 months
        expected_plan_discount = expected_base * PLAN_DISCOUNTS[PlanType.QUARTERLY]
        expected_final = expected_base - expected_plan_discount

        assert result.base_amount == expected_base
        assert result.plan_discount_percentage == PLAN_DISCOUNTS[PlanType.QUARTERLY] * 100
        assert result.plan_discount_amount == expected_plan_discount
        assert result.final_amount == expected_final
        assert result.plan_type == PlanType.QUARTERLY

    def test_yearly_plan_with_sibling_discount(self, pricing_service):
        """Test yearly plan with both plan and sibling discounts."""
        result = pricing_service.calculate_pricing(
            plan_type=PlanType.YEARLY, seats=10, has_sibling_discount=True
        )

        expected_base = BASE_MONTHLY_PRICE * 10 * 12  # 10 seats, 12 months
        expected_plan_discount = expected_base * PLAN_DISCOUNTS[PlanType.YEARLY]
        amount_after_plan_discount = expected_base - expected_plan_discount
        expected_sibling_discount = amount_after_plan_discount * SIBLING_DISCOUNT
        expected_final = amount_after_plan_discount - expected_sibling_discount

        assert result.base_amount == expected_base
        assert result.plan_discount_amount == expected_plan_discount
        assert result.sibling_discount_amount == expected_sibling_discount
        assert result.final_amount == expected_final
        assert result.plan_type == PlanType.YEARLY

    def test_half_yearly_plan(self, pricing_service):
        """Test half-yearly plan pricing."""
        result = pricing_service.calculate_pricing(
            plan_type=PlanType.HALF_YEARLY, seats=1, has_sibling_discount=False
        )

        expected_base = BASE_MONTHLY_PRICE * 1 * 6  # 1 seat, 6 months
        expected_plan_discount = expected_base * PLAN_DISCOUNTS[PlanType.HALF_YEARLY]
        expected_final = expected_base - expected_plan_discount

        assert result.base_amount == expected_base
        assert result.plan_discount_amount == expected_plan_discount
        assert result.final_amount == expected_final
        assert result.plan_type == PlanType.HALF_YEARLY

    def test_discount_info_structure(self, pricing_service):
        """Test that discount info contains all required fields."""
        result = pricing_service.calculate_pricing(
            plan_type=PlanType.YEARLY, seats=5, has_sibling_discount=True
        )

        assert "plan_discount" in result.discount_info
        assert "sibling_discount" in result.discount_info
        assert "total_savings" in result.discount_info
        assert "base_monthly_price" in result.discount_info
        assert "billing_months" in result.discount_info

        plan_discount = result.discount_info["plan_discount"]
        assert "type" in plan_discount
        assert "percentage" in plan_discount
        assert "amount" in plan_discount

        sibling_discount = result.discount_info["sibling_discount"]
        assert "applied" in sibling_discount
        assert "percentage" in sibling_discount
        assert "amount" in sibling_discount

    def test_pricing_precision(self, pricing_service):
        """Test that pricing calculations have correct decimal precision."""
        result = pricing_service.calculate_pricing(
            plan_type=PlanType.MONTHLY, seats=3, has_sibling_discount=False
        )

        # Check that amounts have at most 2 decimal places
        assert result.final_amount.as_tuple().exponent >= -2
        assert result.base_amount.as_tuple().exponent >= -2

    def test_all_plan_types(self, pricing_service):
        """Test all plan types have correct month calculations."""
        plans_and_months = [
            (PlanType.MONTHLY, 1),
            (PlanType.QUARTERLY, 3),
            (PlanType.HALF_YEARLY, 6),
            (PlanType.YEARLY, 12),
        ]

        for plan_type, expected_months in plans_and_months:
            result = pricing_service.calculate_pricing(
                plan_type=plan_type, seats=1, has_sibling_discount=False
            )

            expected_base = BASE_MONTHLY_PRICE * 1 * expected_months
            assert result.base_amount == expected_base
            assert result.discount_info["billing_months"] == expected_months
