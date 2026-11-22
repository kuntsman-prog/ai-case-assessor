"""Экономика кейса: эффект, стоимость владения, окупаемость. Горизонт 36 месяцев."""
from __future__ import annotations

from dataclasses import dataclass

from .model import Case

HORIZON_MONTHS = 36


@dataclass
class Economics:
    hours_saved_month: float
    benefit_month: float
    token_cost_month: float
    infra_month: float
    support_month: float
    run_cost_month: float
    implementation_cost: float
    net_month: float
    tco_3y: float
    benefit_3y: float
    roi_3y: float | None
    payback_months: float | None
    cost_per_operation: float


def evaluate(c: Case) -> Economics:
    ops_used = c.operations_per_month * c.adoption_rate
    hours = ops_used * c.minutes_saved_per_op / 60
    benefit = hours * c.hourly_cost_business + c.extra_benefit_month

    tokens = ops_used * (c.tokens_in_per_op * c.price_in_per_1m + c.tokens_out_per_op * c.price_out_per_1m) / 1_000_000
    support = c.support_hours_month * c.hourly_cost_it
    run = tokens + c.infra_month + support
    impl = c.implementation_hours * c.hourly_cost_it + c.one_time_cost

    net = benefit - run
    tco = impl + run * HORIZON_MONTHS
    benefit_3y = benefit * HORIZON_MONTHS
    roi = (benefit_3y - tco) / tco if tco > 0 else None
    payback = impl / net if net > 0 else None

    return Economics(
        hours_saved_month=round(hours, 1),
        benefit_month=round(benefit),
        token_cost_month=round(tokens),
        infra_month=round(c.infra_month),
        support_month=round(support),
        run_cost_month=round(run),
        implementation_cost=round(impl),
        net_month=round(net),
        tco_3y=round(tco),
        benefit_3y=round(benefit_3y),
        roi_3y=round(roi, 2) if roi is not None else None,
        payback_months=round(payback, 1) if payback is not None else None,
        cost_per_operation=round(run / ops_used, 2) if ops_used else 0.0,
    )
