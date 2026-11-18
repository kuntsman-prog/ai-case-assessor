"""Отчёт по портфелю ИИ-кейсов: HTML для руководства и краткий текст для консоли."""
from __future__ import annotations

import html
from datetime import date

from .economics import HORIZON_MONTHS
from .scoring import Assessment


def rub(x: float | None) -> str:
    return "–" if x is None else f"{x:,.0f}".replace(",", " ") + " ₽"


def facts(a: Assessment) -> dict:
    e = a.economics
    return {
        "кейс": a.case.name,
        "эффект_в_месяц_руб": e.benefit_month,
        "эксплуатация_в_месяц_руб": e.run_cost_month,
        "внедрение_руб": e.implementation_cost,
        "окупаемость_мес": e.payback_months,
        "roi_3_года": e.roi_3y,
        "класс_риска": a.risk.tier_label,
        "блокеры": a.risk.blockers,
        "рекомендация": a.recommendation,
    }


def console(a: Assessment) -> str:
    e = a.economics
    lines = [
        f"{a.case.name}",
        f"  рекомендация: {a.recommendation} ({a.rationale})",
        f"  приоритет {a.priority}: ценность {a.value_score}, реализуемость {a.feasibility_score}, риск {a.risk.tier_label}",
        f"  эффект {rub(e.benefit_month)}/мес, эксплуатация {rub(e.run_cost_month)}/мес, внедрение {rub(e.implementation_cost)}",
        f"  окупаемость {e.payback_months if e.payback_months is not None else '–'} мес, ROI за 3 года {e.roi_3y}",
    ]
    if a.risk.blockers:
        lines.append("  БЛОКЕРЫ: " + "; ".join(a.risk.blockers))
    if a.case.assumptions:
        lines.append("  допущения (значения по умолчанию): " + ", ".join(a.case.assumptions))
    return "\n".join(lines)


CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d2433;--muted:#5d6577;--line:#e3e5ea;--accent:#1f4e9c;
--ok:#1e7a46;--warn:#9a6a00;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root{--bg:#14171d;--card:#1c2028;--ink:#e6e9ef;--muted:#a3abba;--line:#2c323d;--accent:#7aa7ff;
--ok:#5cc58a;--warn:#e0b44a;--bad:#ff8a80}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px}h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:0 0 8px}
.muted{color:var(--muted)}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:16px 0}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600}.num{text-align:right;white-space:nowrap}.wrap{overflow-x:auto}
.tag{display:inline-block;white-space:nowrap;padding:2px 8px;border-radius:999px;font-size:12px;border:1px solid currentColor}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:8px 0}
.kpi{border:1px solid var(--line);border-radius:8px;padding:8px}.kpi b{display:block;font-size:16px}
ul{margin:4px 0 8px 18px;padding:0}
"""


def _rec_class(rec: str) -> str:
    if rec.startswith("Внедрять"):
        return "ok"
    if rec.startswith(("Отклонить", "Не окупается")):
        return "bad"
    return "warn"


def html_report(items: list[Assessment], title: str = "Портфель ИИ-кейсов", summaries: dict[str, str] | None = None) -> str:
    summaries = summaries or {}
    esc = html.escape
    rows = "".join(
        f"<tr><td>{i}</td><td>{esc(a.case.name)}</td><td class='num'>{a.priority}</td>"
        f"<td class='num'>{rub(a.economics.net_month)}</td>"
        f"<td class='num'>{a.economics.payback_months if a.economics.payback_months is not None else '–'}</td>"
        f"<td>{esc(a.risk.tier_label)}</td><td><span class='tag {_rec_class(a.recommendation)}'>{esc(a.recommendation)}</span></td></tr>"
        for i, a in enumerate(items, 1)
    )
    cards = []
    for a in items:
        e, r = a.economics, a.risk
        req = "".join(f"<p><b>{k}</b></p><ul>" + "".join(f"<li>{esc(x)}</li>" for x in v) + "</ul>" for k, v in r.requirements.items() if v)
        blockers = "".join(f"<li class='bad'>{esc(b)}</li>" for b in r.blockers)
        summary = f"<p>{esc(summaries[a.case.name])}</p>" if a.case.name in summaries else ""
        assumptions = (f"<p class='muted'>Допущения (значения по умолчанию): {esc(', '.join(a.case.assumptions))}</p>"
                       if a.case.assumptions else "")
        cards.append(f"""
<section class="card">
  <h2>{esc(a.case.name)} <span class="tag {_rec_class(a.recommendation)}">{esc(a.recommendation)}</span></h2>
  <p class="muted">{esc(a.case.process)}</p>{summary}
  <div class="grid">
    <div class="kpi">Эффект в месяц<b>{rub(e.benefit_month)}</b></div>
    <div class="kpi">Эксплуатация в месяц<b>{rub(e.run_cost_month)}</b></div>
    <div class="kpi">Внедрение<b>{rub(e.implementation_cost)}</b></div>
    <div class="kpi">Окупаемость<b>{e.payback_months if e.payback_months is not None else '–'} мес.</b></div>
    <div class="kpi">TCO за {HORIZON_MONTHS} мес.<b>{rub(e.tco_3y)}</b></div>
    <div class="kpi">ROI за {HORIZON_MONTHS} мес.<b>{e.roi_3y if e.roi_3y is not None else '–'}</b></div>
    <div class="kpi">Стоимость операции<b>{e.cost_per_operation} ₽</b></div>
    <div class="kpi">Сэкономлено часов в месяц<b>{e.hours_saved_month}</b></div>
  </div>
  <p><b>Класс риска: {esc(r.tier_label)}.</b> {esc('; '.join(r.reasons))}</p>
  {'<ul>' + blockers + '</ul>' if blockers else ''}
  <p><b>Обоснование:</b> {esc(a.rationale)}. Ценность {a.value_score} из 5, реализуемость {a.feasibility_score} из 5.</p>
  <details><summary>Требования (по функциям NIST AI RMF)</summary>{req}</details>
  {assumptions}
</section>""")
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>{CSS}</style></head>
<body><main>
<h1>{esc(title)}</h1>
<p class="muted">Сформировано {date.today():%d.%m.%Y}. Приоритет = 0,6 × ценность + 0,4 × реализуемость − штраф за риск. Горизонт {HORIZON_MONTHS} мес.</p>
<section class="card"><h2>Очередь внедрения</h2><div class="wrap"><table>
<tr><th>#</th><th>Кейс</th><th class="num">Приоритет</th><th class="num">Чистый эффект/мес</th><th class="num">Окупаемость, мес.</th><th>Риск</th><th>Рекомендация</th></tr>
{rows}</table></div></section>
{''.join(cards)}
</main></body></html>"""
