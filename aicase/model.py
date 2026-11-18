"""Описание ИИ-кейса. Все поля проверяются; значения по умолчанию помечаются как допущения."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DataSensitivity(str, Enum):
    public = "public"            # открытые данные
    internal = "internal"        # внутренние документы
    confidential = "confidential"  # коммерческая или банковская тайна
    personal = "personal"        # персональные данные клиентов или сотрудников


class Audience(str, Enum):
    internal = "internal"  # пользуются сотрудники
    clients = "clients"    # ИИ напрямую взаимодействует с клиентами


class Autonomy(str, Enum):
    assistant = "assistant"    # подсказывает, решение за человеком
    agent = "agent"            # выполняет действия через инструменты под контролем человека
    autonomous = "autonomous"  # действует без подтверждения человека


class Deployment(str, Enum):
    local = "local"            # модель в контуре компании
    russian_cloud = "russian_cloud"
    foreign_api = "foreign_api"


class DecisionImpact(str, Enum):
    none = "none"              # справка, черновик
    internal = "internal"      # влияет на внутренние процессы
    client = "client"          # влияет на права или условия для клиента (одобрение, ставка, отказ)


class Case(BaseModel):
    name: str
    process: str = Field(description="бизнес-процесс и что именно делает ИИ")

    # Эффект
    operations_per_month: int = Field(ge=0, description="сколько операций в месяц затрагивает решение")
    minutes_saved_per_op: float = Field(ge=0, description="сколько минут экономит одна операция")
    adoption_rate: float = Field(0.7, ge=0, le=1, description="доля операций, где решение реально используют")
    hourly_cost_business: float = Field(1200, ge=0, description="стоимость часа сотрудника бизнеса, руб.")
    extra_benefit_month: float = Field(0, ge=0, description="прочий измеримый эффект в месяц, руб.")

    # Затраты на эксплуатацию
    tokens_in_per_op: int = Field(2000, ge=0)
    tokens_out_per_op: int = Field(500, ge=0)
    price_in_per_1m: float = Field(150, ge=0, description="руб. за 1 млн входных токенов")
    price_out_per_1m: float = Field(600, ge=0, description="руб. за 1 млн выходных токенов")
    infra_month: float = Field(0, ge=0, description="GPU, подписки, лицензии в месяц, руб.")
    support_hours_month: float = Field(16, ge=0)
    hourly_cost_it: float = Field(2500, ge=0)

    # Внедрение
    implementation_hours: float = Field(240, ge=0)
    one_time_cost: float = Field(0, ge=0)

    # Риск и ИБ
    data_sensitivity: DataSensitivity = DataSensitivity.internal
    audience: Audience = Audience.internal
    autonomy: Autonomy = Autonomy.assistant
    deployment: Deployment = Deployment.local
    decision_impact: DecisionImpact = DecisionImpact.none
    prohibited_practice: bool = Field(False, description="манипуляция, социальный скоринг и т.п.")

    # Реализуемость, 1 (плохо) .. 5 (отлично)
    data_readiness: int = Field(3, ge=1, le=5)
    integration_simplicity: int = Field(3, ge=1, le=5)

    # Поля, значения которых не были заданы явно (заполняются при загрузке)
    assumptions: list[str] = Field(default_factory=list)


FIELD_LABELS = {
    "adoption_rate": "доля использования", "hourly_cost_business": "стоимость часа сотрудника",
    "tokens_in_per_op": "входные токены на операцию",
    "tokens_out_per_op": "выходные токены на операцию", "price_in_per_1m": "цена входных токенов",
    "price_out_per_1m": "цена выходных токенов", "infra_month": "инфраструктура и подписки",
    "support_hours_month": "часы сопровождения", "hourly_cost_it": "стоимость часа ИТ",
    "implementation_hours": "трудозатраты на внедрение",
    "data_sensitivity": "чувствительность данных", "audience": "аудитория", "autonomy": "автономность",
    "deployment": "размещение модели", "decision_impact": "влияние на решения",
    "data_readiness": "готовность данных", "integration_simplicity": "простота интеграции",
}


def case_from_dict(data: dict) -> Case:
    """Создаёт кейс и фиксирует, какие поля взяты по умолчанию."""
    case = Case(**data)
    required = {"name", "process", "operations_per_month", "minutes_saved_per_op"}
    defaulted = [FIELD_LABELS[f] for f in Case.model_fields if f in FIELD_LABELS and f not in data]
    case.assumptions = defaulted
    return case
