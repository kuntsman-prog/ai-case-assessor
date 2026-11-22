"""Приоритет и рекомендация. Критерии открыты и одинаковы для всех кейсов."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .economics import Economics, evaluate
from .model import Case
from .risk import RiskAssessment, assess

RISK_PENALTY = {"minimal": 0.0, "limited": 0.5, "high": 1.5, "unacceptable": 5.0}
MAX_PAYBACK_MONTHS = 24


@dataclass
class Assessment:
    case: Case
    economics: Economics
    risk: RiskAssessment
    value_score: float
    feasibility_score: float
    priority: float
    recommendation: str
    rationale: str


def value_score(e: Economics) -> float:
    """0..5 по чистому эффекту в месяц (логарифмическая шкала: 10 тыс. руб. = 1, 1 млн руб. = 5)."""
    if e.net_month <= 0:
        return 0.0
    return round(max(0.0, min(5.0, (math.log10(e.net_month) - 3.75) * 2)), 2)


def assess_case(c: Case) -> Assessment:
    e = evaluate(c)
    r = assess(c)
    v = value_score(e)
    f = round((c.data_readiness + c.integration_simplicity) / 2, 2)
    priority = round(0.6 * v + 0.4 * f - RISK_PENALTY[r.tier], 2)

    if r.blockers:
        rec, why = "Отклонить до устранения блокеров", "; ".join(r.blockers)
    elif e.net_month <= 0:
        rec, why = "Не окупается", "эксплуатация дороже эффекта"
    elif e.payback_months and e.payback_months > MAX_PAYBACK_MONTHS:
        rec, why = "Не окупается", f"срок окупаемости {e.payback_months} мес. больше порога {MAX_PAYBACK_MONTHS}"
    elif r.tier == "high":
        rec, why = "Пилот с контролем человека", "высокий риск: решение только после подтверждения человеком"
    elif f < 2.5:
        rec, why = "Подготовить данные и интеграции", f"низкая реализуемость ({f} из 5)"
    elif e.payback_months and e.payback_months <= 6 and priority >= 3:
        rec, why = "Внедрять в первую очередь", f"окупаемость {e.payback_months} мес., приоритет {priority}"
    else:
        rec, why = "Пилот", f"окупаемость {e.payback_months} мес., приоритет {priority}"

    return Assessment(c, e, r, v, f, priority, rec, why)


STATUS_ORDER = {"Внедрять в первую очередь": 0, "Пилот": 1, "Пилот с контролем человека": 1,
                "Подготовить данные и интеграции": 2, "Не окупается": 3, "Отклонить до устранения блокеров": 4}


def rank(cases: list[Case]) -> list[Assessment]:
    """Сначала кейсы, которые можно внедрять; внутри группы по убыванию приоритета."""
    return sorted((assess_case(c) for c in cases), key=lambda a: (STATUS_ORDER[a.recommendation], -a.priority))
