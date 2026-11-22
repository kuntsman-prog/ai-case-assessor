import json
from pathlib import Path

import pytest
import yaml

from aicase.economics import evaluate
from aicase.llm import extract_case
from aicase.model import case_from_dict
from aicase.report import html_report
from aicase.risk import assess
from aicase.scoring import assess_case, rank

CASES = Path(__file__).resolve().parent.parent / "examples" / "cases"


def base(**kw):
    data = {"name": "t", "process": "p", "operations_per_month": 1000, "minutes_saved_per_op": 6}
    data.update(kw)
    return case_from_dict(data)


def test_economics_formula():
    c = base(adoption_rate=1.0, hourly_cost_business=1000, price_in_per_1m=0, price_out_per_1m=0,
             support_hours_month=0, implementation_hours=100, hourly_cost_it=2000)
    e = evaluate(c)
    assert e.hours_saved_month == 100           # 1000 операций * 6 минут
    assert e.benefit_month == 100_000
    assert e.implementation_cost == 200_000
    assert e.payback_months == 2.0


def test_risk_tiers():
    assert assess(base()).tier == "minimal"
    assert assess(base(audience="clients")).tier == "limited"
    assert assess(base(decision_impact="client")).tier == "high"
    assert assess(base(prohibited_practice=True)).tier == "unacceptable"


def test_blocker_personal_data_foreign_api():
    r = assess(base(data_sensitivity="personal", deployment="foreign_api"))
    assert r.blockers
    assert assess_case(base(data_sensitivity="personal", deployment="foreign_api")).recommendation.startswith("Отклонить")


def test_unprofitable_case():
    a = assess_case(base(operations_per_month=10, infra_month=50_000))
    assert a.recommendation == "Не окупается"


def test_high_risk_requires_human():
    a = assess_case(base(decision_impact="client", operations_per_month=5000, minutes_saved_per_op=20))
    assert a.recommendation == "Пилот с контролем человека"
    assert any("подтверждение человеком" in x for x in a.risk.requirements["Manage"])


def test_portfolio_order_blocked_last():
    items = rank([case_from_dict(yaml.safe_load(f.read_text(encoding="utf-8"))) for f in sorted(CASES.glob("*.yaml"))])
    assert items[0].recommendation == "Внедрять в первую очередь"
    assert items[-1].recommendation.startswith("Отклонить")


def test_assumptions_are_reported():
    assert "стоимость часа ИТ" in base().assumptions


def test_llm_extraction_with_retry():
    calls = []

    def fake_chat(messages):
        calls.append(messages)
        if len(calls) == 1:
            return '{"name": "x", "process": "y", "operations_per_month": "много"}'  # неверный тип
        return json.dumps({"name": "Ассистент", "process": "ответы по базе знаний",
                           "operations_per_month": 5000, "minutes_saved_per_op": 4,
                           "data_sensitivity": "internal", "unknown_field": 1})

    case = extract_case("описание", chat=fake_chat)
    assert case.operations_per_month == 5000
    assert len(calls) == 2                       # одна повторная попытка с текстом ошибки
    assert "не прошёл проверку" in calls[1][-1]["content"]


def test_llm_extraction_fails_cleanly():
    with pytest.raises(ValueError):
        extract_case("описание", chat=lambda m: "нет json")


def test_html_report_has_no_em_dash():
    items = rank([base(name="a"), base(name="b", decision_impact="client")])
    html = html_report(items)
    assert "\u2014" not in html and "Очередь внедрения" in html
