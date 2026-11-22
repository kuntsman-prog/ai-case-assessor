"""Класс риска и требования ИБ.

Классы риска построены по логике EU AI Act (недопустимый, высокий, ограниченный,
минимальный) и адаптированы под внутреннюю политику компании. Требования
сгруппированы по функциям NIST AI RMF: Govern, Map, Measure, Manage.
Это инструмент первичной оценки, а не юридическое заключение.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .model import Audience, Autonomy, Case, DataSensitivity, DecisionImpact, Deployment

TIER_LABELS = {
    "unacceptable": "Недопустимый",
    "high": "Высокий",
    "limited": "Ограниченный",
    "minimal": "Минимальный",
}


@dataclass
class RiskAssessment:
    tier: str
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    requirements: dict[str, list[str]] = field(default_factory=dict)

    @property
    def tier_label(self) -> str:
        return TIER_LABELS[self.tier]


def assess(c: Case) -> RiskAssessment:
    reasons, blockers = [], []
    req = {"Govern": [], "Map": [], "Measure": [], "Manage": []}

    # Класс риска
    if c.prohibited_practice:
        tier = "unacceptable"
        reasons.append("Запрещённая практика (манипуляция, социальный скоринг и т.п.)")
        blockers.append("Кейс относится к недопустимым практикам применения ИИ")
    elif c.decision_impact == DecisionImpact.client:
        tier = "high"
        reasons.append("ИИ влияет на решения, затрагивающие права или условия для клиента")
    elif c.autonomy == Autonomy.autonomous and c.audience == Audience.clients:
        tier = "high"
        reasons.append("ИИ действует автономно в отношении клиентов")
    elif c.audience == Audience.clients:
        tier = "limited"
        reasons.append("ИИ напрямую взаимодействует с клиентами")
    elif c.autonomy != Autonomy.assistant:
        tier = "limited"
        reasons.append("ИИ выполняет действия через инструменты")
    else:
        tier = "minimal"
        reasons.append("Внутренний помощник, решение остаётся за сотрудником")

    # Блокеры по данным
    if c.data_sensitivity == DataSensitivity.personal and c.deployment == Deployment.foreign_api:
        blockers.append("Передача персональных данных во внешний зарубежный сервис: нарушение требований о ПДн и локализации")
    if c.data_sensitivity == DataSensitivity.confidential and c.deployment == Deployment.foreign_api:
        blockers.append("Конфиденциальные данные во внешнем зарубежном сервисе: требуется локальная модель или российское облако")

    # Govern: политика и ответственность
    req["Govern"].append("Назначить владельца кейса со стороны бизнеса и ответственного за модель")
    req["Govern"].append("Внести кейс в реестр ИИ-решений компании")
    if tier == "high":
        req["Govern"].append("Согласовать кейс с ИБ, юристами и комплаенсом до пилота")

    # Map: данные и контекст
    if c.data_sensitivity == DataSensitivity.personal:
        req["Map"].append("Оценка обработки ПДн (152-ФЗ): цели, состав, сроки, правовое основание")
        req["Map"].append("Маскирование ПДн в запросах, ответах и журналах")
    if c.data_sensitivity in (DataSensitivity.confidential, DataSensitivity.personal):
        req["Map"].append("Разграничение доступа к данным на уровне документов до подачи в модель")
    if c.deployment == Deployment.russian_cloud:
        req["Map"].append("Договор с облачным провайдером: локализация, запрет обучения на данных компании")

    # Measure: качество и контроль
    req["Measure"].append("Набор проверок качества до запуска и регулярный повторный прогон")
    if c.audience == Audience.clients or c.autonomy != Autonomy.assistant:
        req["Measure"].append("Тестирование на инъекции промпта и обход ограничений")
    if tier == "high":
        req["Measure"].append("Проверка на смещения и дискриминацию, объяснимость решений")

    # Manage: эксплуатация
    req["Manage"].append("Журналирование запросов и ответов с маскированием, хранение по регламенту")
    if c.audience == Audience.clients:
        req["Manage"].append("Информировать клиента, что он взаимодействует с ИИ")
    if c.autonomy != Autonomy.assistant:
        req["Manage"].append("Минимальные права инструментов агента, журнал действий, лимиты операций")
    if c.autonomy == Autonomy.autonomous or tier == "high":
        req["Manage"].append("Обязательное подтверждение человеком значимых действий и решений")
    req["Manage"].append("Мониторинг потребления ресурсов и бюджета кейса")

    return RiskAssessment(tier=tier, reasons=reasons, blockers=blockers, requirements=req)
